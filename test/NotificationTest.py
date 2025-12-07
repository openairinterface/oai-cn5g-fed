import os
import sys
import logging
from pymongo import MongoClient, errors
import re
from common import *
from docker_api import DockerApi
from image_tags import image_tags
import json


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def mongo_access(service_type: str):
    try:
        logging.getLogger('pymongo').setLevel(logging.INFO)
        client = MongoClient('mongodb://localhost:27017/')
        client.server_info()
        db = client['notification_db']
        if service_type == "amf notifications":
            return db['amf_notifications']
        elif service_type == "smf notifications":
            return db['smf_notifications']
        elif service_type == "smf traffic report":
            return db['smf_notification_traffic']
        elif service_type == "amf location report":
            return db['amf_location_notification']
        else:
            raise ValueError(f"Invalid service type: {service_type}")
    except errors.ServerSelectionTimeoutError:
        logger.error(f"Failed to connect to MongoDB server")
        raise AssertionError("Failed to connect to MongoDB server")
    
def extract_ue_info_from_SMF_logs(logs, nb_of_users):
    smf_contexts = re.findall(r'SMF CONTEXT:.*?(?=SMF CONTEXT:|$)', logs, re.DOTALL)
    parsed_log_data = []

    for context in smf_contexts:
        parsed_context = {}
        lines = context.split('\n')
        for line in lines:
            if "SUPI:" in line:
                parsed_context['SUPI'] = line.split(':')[1].strip()
            if "PDU Session ID:" in line:
                parsed_context['PDU Session ID'] = line.split(':')[1].strip()
            if "DNN:" in line:
                parsed_context['DNN'] = line.split(':')[1].strip()
            if "PAA IPv4:" in line:
                parsed_context['PAA IPv4'] = line.split(':')[1].strip()
            if "PDN type:" in line:
                parsed_context['PDN type'] = line.split(':')[1].strip()
            if "SEID:" in line:
                parsed_context['SEID'] = line.split(':')[1].strip()
        parsed_log_data.append(parsed_context)
    if len(parsed_log_data) != nb_of_users:
        logger.warning(f"Number of SMF contexts in logs ({len(parsed_log_data)}) does not match the number of users added ({nb_of_users})")
        if len(parsed_log_data) == 0:
            logger.error(f"No SMF contexts found in logs.")
            raise Exception("No SMF contexts found in logs. PDU Session ongoing")
    return parsed_log_data
    
def check_smf_callback(logs, nb_of_users):
    try:
        smf_collection = mongo_access("smf notifications")
        parsed_log_data =  extract_ue_info_from_SMF_logs(logs,nb_of_users)
        callback_data = []
        for document in smf_collection.find():
            for report in document["eventNotifs"]:
                supi = report["supi"]
                pdu_session_id = report["pduSeId"]
                dnn = report["dnn"]
                paa_ipv4 = report["adIpv4Addr"]
                ip_session_type = report["pduSessType"]
                callback_data.append({
                    'SUPI': supi,
                    'PDU Session ID': f"{pdu_session_id}",
                    'DNN': dnn,
                    'PAA IPv4': paa_ipv4,
                    'PDN type': ip_session_type
                })
        if parsed_log_data != []: 
            for log_entry in parsed_log_data:
                match_found = False
                for callback_entry in callback_data:
                    if (log_entry['SUPI'] == callback_entry['SUPI'] and
                        log_entry['PDU Session ID'] == callback_entry['PDU Session ID'] and
                        log_entry['DNN'] == callback_entry['DNN'] and
                        log_entry['PAA IPv4'] == callback_entry['PAA IPv4']):
                        match_found = True
                        break
                if not match_found:
                    logger.error(f"Mismatch found for SUPI: {log_entry['SUPI']}, Callback data: {callback_entry}, logs data: {log_entry}")
                    raise Exception(f"Mismatch found for SUPI: {log_entry['SUPI']}")
            logger.info(f"All SMF contexts match the callback data.{callback_data}, logs data: {parsed_log_data}")

        else :

            logger.error(f"No SMF contexts found in logs.")
            raise Exception("No SMF contexts found in logs.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e

def amf_report_from_handler(service_type: str):
    try:
        amf_collection = mongo_access(service_type)
        latest_imsi_events = {}
        for document in amf_collection.find():
            for report in document["reportList"]:
                supi = report["supi"]
                rm_state = report["rmInfoList"][0]["rmState"]
                timestamp = report["timeStamp"]
                ran_ue_ngap_id = report.get("ranUeNgapId", "")
                amf_ue_ngap_id = report.get("amfUeNgapId", "")

                if supi.startswith("imsi-"):
                    supi = supi[5:]
                if supi not in latest_imsi_events or timestamp > latest_imsi_events[supi]['timestamp']:
                    latest_imsi_events[supi] = {
                        'rm_state': rm_state,
                        'timestamp': timestamp,
                        'ran_ue_ngap_id': ran_ue_ngap_id,
                        'amf_ue_ngap_id': amf_ue_ngap_id,
                    }
        latest_registered_imsis = [
            {'imsi': imsi, 'details': event}
            for imsi, event in latest_imsi_events.items()
        ]
        return latest_registered_imsis
    except Exception as e:
        logger.error(f"Failed to get IMSIs from handler collection: {e}")
        raise e


def get_location_report_info(service_type: str):
    try:
        amf_collection = mongo_access(service_type)
        latest_location_events = {}
        for document in amf_collection.find():
            for report in document["reportList"]:
                if report["type"] == "LOCATION_REPORT":
                    supi = report["supi"]
                    location_info = report.get("location", {})
                    nr_location = location_info.get("nrLocation", {})
                    global_gnb_id = nr_location.get("globalGnbId", {})
                    gnb_value = global_gnb_id.get("gNbId", {}).get("gNBValue", "")
                    plmn_id = global_gnb_id.get("plmnId", {})
                    mcc = plmn_id.get("mcc", "")
                    mnc = plmn_id.get("mnc", "")
                    nr_cell_id = nr_location.get("ncgi", {}).get("nrCellId", "")
                    tac = nr_location.get("tai", {}).get("tac", "")
                    timestamp = report["timeStamp"]

                    if supi.startswith("imsi-"):
                        supi = supi[5:]
                    if supi not in latest_location_events or timestamp > latest_location_events[supi]['timestamp']:
                        latest_location_events[supi] = {
                            'gnb_value': gnb_value,
                            'plmn_id': f"{mcc}, {mnc}",
                            'nr_cell_id': nr_cell_id,
                            'tac': tac,
                            'timestamp': timestamp
                        }
        latest_location_reports = [
            {'imsi': imsi, 'details': event}
            for imsi, event in latest_location_events.items()
        ]
        return latest_location_reports
    except Exception as e:
        logger.error(f"Failed to get location reports from handler collection: {e}")
        raise e

def check_AMF_reg_callback(nb_of_users, logs):
    try:
        report_from_handler = amf_report_from_handler(service_type="amf notifications")
        report_from_AMF = extract_ue_info_from_AMF_logs(logs, nb_of_users)
        handler_dict = {report['imsi']: report['details'] for report in report_from_handler}
        i = 0
        for report in report_from_AMF:
            imsi = report['IMSI']
            if report['5GMM State'] != '5GMM-REGISTERED':     #handle the case where its initiated, it shouldnt raise an error
                logger.warning(f"UE {imsi} is {report['5GMM State']}")
                i=+1
                continue
                # raise Exception(f"UE {imsi} is {report['5GMM State']}")
            else:
                if imsi in handler_dict:
                    handler_details = handler_dict[imsi]
                    if (int(report['RAN UE NGAP ID'],16) == int(handler_details['ran_ue_ngap_id']) and
                        int(report['AMF UE NGAP ID'],16) == int(handler_details['amf_ue_ngap_id']) and
                        handler_details['rm_state'] == "REGISTERED"):
                        logger.info(f"UE {imsi} matches handler data: ran_ue_ngap_id: {int(handler_details['ran_ue_ngap_id'])} and logs data: RAN UE NGAP ID: {int(report['RAN UE NGAP ID'],16)}, handler: amf_ue_ngap_id: {int(handler_details['amf_ue_ngap_id'])} and logs data: AMF UE NGAP ID: {int(report['AMF UE NGAP ID'],16)}, handler RM State: {handler_details['rm_state']}, logs RM State: REGISTERED")
                        continue
                    else:
                        logger.error(f"{imsi} callback data does not match AMF data. Callback: ran_ue_ngap_id: {int(handler_details['ran_ue_ngap_id'])}, logs data: RAN UE NGAP ID: {int(report['RAN UE NGAP ID'],16)}, Callback: amf_ue_ngap_id: {int(handler_details['amf_ue_ngap_id'])}, logs data: AMF UE NGAP ID: {int(report['AMF UE NGAP ID'],16)}, Callback RM State: {handler_details['rm_state']}, logs RM State: REGISTERED")
                        raise Exception(f"Data mismatch for IMSI {imsi}.")
                else:
                    logger.error(f"UE {imsi} not found in handler collection.")
                    raise Exception(f"UE {imsi} not found in handler collection.")
        if i == nb_of_users:
            logger.error(f"All UEs weren't added succesfully.")
            raise Exception(f"All UEs werent added succesfully.")
        logger.info("AMF UE Data match the callback data.")
    except Exception as e:
        logger.error(f"Failed to check latest registered IMSIs: {e}")
        raise e

def check_AMF_dereg_callback(logs,nb_of_users):
    try:
        report_from_handler = amf_report_from_handler(service_type="amf notifications")
        report_from_AMF = extract_ue_info_from_AMF_logs(logs, nb_of_users)    
        handler_dict = {report['imsi']: report['details'] for report in report_from_handler}
        i = 0
        for report in report_from_AMF:
            imsi = report['IMSI']
            if report['5GMM State'] != '5GMM-DEREGISTERED':     #if it still initiated no error should be raised as awe are testing callbacks.
                logger.warning(f"UE {imsi} is {report['5GMM State']}")
                i+=1
                continue
                # raise Exception(f"UE {imsi} is {report['5GMM State']}")
            else:
                if imsi in handler_dict:
                    handler_details = handler_dict[imsi]
                    if (int(report['RAN UE NGAP ID'],16) == int(handler_details['ran_ue_ngap_id']) and
                        int(report['AMF UE NGAP ID'],16) == int(handler_details['amf_ue_ngap_id']) and
                        handler_details['rm_state'] == "DEREGISTERED"):
                        logger.info(f"UE {imsi} matches handler data Callback ran_ue_ngap_id: {int(handler_details['ran_ue_ngap_id'])}, logs data: RAN UE NGAP ID:{int(report['RAN UE NGAP ID'],16)}, Callback: amf_ue_ngap_id': {int(handler_details['amf_ue_ngap_id'])}, logs data: AMF UE NGAP ID:{int(report['AMF UE NGAP ID'],16)}, Handler RM State: {handler_details['rm_state']}, Logs RM State: DEREGISTERED")
                        continue
                    else:
                        logger.error(f"{imsi} callback data does not match AMF data. Callback: ran_ue_ngap_id: {int(handler_details['ran_ue_ngap_id'])}, logs data: RAN UE NGAP ID:{int(report['RAN UE NGAP ID'],16)}, Callback: amf_ue_ngap_id': {int(handler_details['amf_ue_ngap_id'])}, logs data: AMF UE NGAP ID:{int(report['AMF UE NGAP ID'],16)}, Handler RM State: {handler_details['rm_state']}, Logs RM State: DEREGISTERED")
                        raise Exception(f"Data mismatch for IMSI {imsi}.")
                else:
                    logger.error(f"UE {imsi} not found in handler collection.")
                    raise Exception(f"UE {imsi} not found in handler collection.")
        if i == nb_of_users:
            logger.error(f"All UEs weren't removed succesfully.")
            raise Exception(f"All UEs werent removed succesfully")
        logger.info("AMF UE Data match the callback data.")
    except Exception as e:
        logger.error(f"Failed to check latest deregistered IMSIs: {e}")
        raise e

def check_AMF_Location_report_callback(logs, nb_of_users):
    try:
        if logs == "":
            logger.error("No location reports found in logs.")
            raise Exception("No location reports found in logs.")
        report_from_handler = get_location_report_info(service_type="amf location report")
        report_from_amf = extract_ue_info_from_AMF_logs(logs, nb_of_users)
        handler_dict = {report['imsi']: report['details'] for report in report_from_handler}
        if len(report_from_handler) != nb_of_users:
            logger.warning(f"Number of UE Location Reports ({len(report_from_handler)}) does not match the number of users added ({nb_of_users})")
            if len(report_from_handler) == 0:
                logger.error(f"No location reports notifications received")
                raise Exception(f"No location reports notifications received")
        for report in report_from_amf:
            imsi = report['IMSI']
            if imsi in handler_dict:
                handler_details = handler_dict[imsi]
                if int(handler_details['nr_cell_id'],10) != int(report['Cell Id'],16):
                    logger.error(f"IMSI {imsi} NR Cell ID mismatch: Handler({hex(int(handler_details['nr_cell_id']))}) != AMF({report['Cell Id']})")
                    raise Exception(f"Data mismatch for IMSI {imsi}: NR Cell ID mismatch.")
                else:
                    logger.info(f"IMSI {imsi} matches handler NR Cell ID: {hex(int(handler_details['nr_cell_id']))} and logs cell id: {report['Cell Id']}")
            else:
                logger.warning(f"UE {imsi} not found in handler collection.")
                # raise Exception(f"UE {imsi} not found in handler collection.")

        logger.info("All callback data matches the AMF UEs location Data.")
    except Exception as e:
        logger.error(f"Failed to check latest location reports: {e}")
        raise e


def extract_ue_info_from_AMF_logs(logs, nb_of_users):
    try:
        if not logs.strip():
            raise Exception("No logs found.")
        cleaned_logs = logs.strip()
        ue_info_lines = cleaned_logs.split('\n')
        start_index = None
        end_index = None
        for i, line in enumerate(ue_info_lines):
            if 'UEs\' Information' in line:
                start_index = i + 2
            elif '|-----------------------------------------------------------------------------------------------------------------------------------------------------------|' in line:
                end_index = i
        if start_index is None or end_index is None:
            raise ValueError("Could not locate UE information table in logs.")
        raw_headers = [header.strip() for header in ue_info_lines[start_index - 1].split('|')[1:-1]]
        ue_info_lines = ue_info_lines[start_index:end_index]
        ue_info_list = []
        for line in ue_info_lines[:nb_of_users]:
            values = [value.strip() for value in line.split('|')[1:-1]]
            ue_info = dict(zip(raw_headers, values))
            ue_info_list.append(ue_info)
        if len(ue_info_list) != nb_of_users:
            logging.warning(f"Number of UEs in logs ({len(ue_info_list)}) does not match the number of users added ({nb_of_users}).")
            if len(ue_info_list) == 0:
                raise ValueError("No UEs found in logs.")
        return ue_info_list
    except Exception as e:
        logger.error(f"Failed to extract UE information from logs: {e}")
        raise e

def extract_mobility_info_from_logs(eng_logs,amf_logs):
    mobsim_info = []
    amf_info = []
    log_lines = eng_logs.splitlines()
    for i in range(len(log_lines) - 2):
        line1 = log_lines[i]
        line2 = log_lines[i + 1]
        line3 = log_lines[i + 2]
        if (
            "Handover event for UE" in line1 and
            "Handover procedure initiated" in line2 and
            "Current cell changed" in line3
        ):
            supi_pattern = r'imsi-\d+'
            src_nci_pattern = r'src-NCI \[(\-?\d+)\]'
            dst_nci_pattern = r'dst-NCI \[(\-?\d+)\]'
            current_cell_pattern = r'Current cell changed \[(\d+)\]'

            supi = re.search(supi_pattern, line1).group(0)
            src_nci = int(re.search(src_nci_pattern, line1).group(1))
            dst_nci = int(re.search(dst_nci_pattern, line1).group(1))
            current_cell = int(re.search(current_cell_pattern, line3).group(1))

            mobsim_info.append({
                'supi': supi,
                'src-NCI': src_nci,
                'dst-NCI': dst_nci,
                'current_cell': current_cell
            })
    pattern = re.compile(
              r'HandoverNotifyIEs\s*::=\s*\{.*?'
              r'id:\s*121\s*'
              r'criticality:\s*1\s*\(ignore\).*?'
              r'nRCellIdentity:\s*([0-9A-F\s]+)\s*\(',
              re.DOTALL
             )
    matches = pattern.findall(amf_logs)
    if len(matches) == 0:
        raise ValueError("failed to change location by mobsim location simulatory.")
    else:
        amf_info = [match.strip() for match in matches][-1]
        amf_current_cell = int(amf_info.replace(' ', ''),16)
        return mobsim_info, amf_current_cell

def check_AMF_location_mobility_report_callback():
    """
    The test support one UE only
    """
    try:
        amf_logs = subprocess.check_output(['docker', 'logs', 'oai-amf'], text=True)
        eng_logs = subprocess.check_output(['docker', 'logs', 'mobsim-eng'], text=True)
        mobsim_info, amf_current_cell_id = extract_mobility_info_from_logs(eng_logs,amf_logs)
        amf_current_cell_id = amf_current_cell_id >> 4
        logging.info(f"Test will check the mobility of UE from CEll ID {hex(mobsim_info[-1]['src-NCI'])} to Cell ID {hex(mobsim_info[-1]['dst-NCI'])}")
        if int(mobsim_info[-1]['current_cell']) != amf_current_cell_id:
            logger.error(f"Missmatch in AMF Logs and Mobility Simulator logs for SUPI: AMF current Cell ID = {hex(amf_current_cell_id)}, Mobsim logs: Current Cell ID = {hex(mobsim_info[-1]['current_cell'])}")
            raise Exception(f"Missmatch in AMF Logs and Mobility Simulator logs for SUPI: AMF current Cell ID = {hex(amf_current_cell_id)}, Mobsim logs: Current Cell ID = {hex(mobsim_info[-1]['current_cell'])}")
        logger.info(f"Mobility data matches between AMF and Mobility Simulator for all UEs, AMF current Cell ID = {hex(amf_current_cell_id)}, Mobsim logs: Current Cell ID = {hex(mobsim_info[-1]['current_cell'])}")
        handler_data = get_location_report_info(service_type="amf location report")[-1]
        # amf_current_cell_id = amf_current_cell_id << 4
        if amf_current_cell_id!= int(handler_data['details']['nr_cell_id']):
            logger.error(f"Missmatch in AMF Logs and Handler data, AMF current Cell ID = {hex(amf_current_cell_id)}, Handler data: Current Cell ID = {handler_data['details']['nr_cell_id']}")
            raise Exception(f"Missmatch in AMF Logs and Handler data, AMF current Cell ID = {hex(amf_current_cell_id)}, Handler data: Current Cell ID = {handler_data['details']['nr_cell_id']}")
        logger.info(f"Mobility data matches between AMF and Handler for all UEs, AMF current Cell ID = {hex(amf_current_cell_id)}, Handler data: Current Cell ID = {hex(int(handler_data['details']['nr_cell_id']))}")
    except Exception as e:
        logger.error(f"Failed to check mobility data: {e}")
        raise e

def get_traffic_data_from_handler(ue_supi):
    smf_traffic_collection = mongo_access("smf traffic report")
    query = {
        'eventNotifs.supi': ue_supi,
        '$or': [
            {'eventNotifs.customized_data.Usage Report.Volume.Total': {'$ne': 0}},
            {'eventNotifs.customized_data.Usage Report.Volume.Uplink': {'$ne': 0}},
            {'eventNotifs.customized_data.Usage Report.Volume.Downlink': {'$ne': 0}}
        ]
    }
    try:
        records = smf_traffic_collection.find(query)
        if smf_traffic_collection.count_documents(query) == 0:
            raise ValueError(f"No records with non-zero traffic found for SUPI: {ue_supi}")
    except Exception as e:
        logger.error(f"Failed to retrieve records from MongoDB: {str(e)}")
        raise RuntimeError(f"Failed to retrieve records from MongoDB: {str(e)}") from e

    result_list = []
    for record in records:
        for event in record.get('eventNotifs', []):
            usage_report = event.get('customized_data', {}).get('Usage Report', {})
            seid = usage_report.get('SEID')
            ur_seqn = usage_report.get('UR-SEQN')
            volume_total = usage_report.get('Volume', {}).get('Total')
            nop_total = usage_report.get('NoP', {}).get('Total')

            result_list.append({
                'SEID': seid,
                'UR-SEQN': ur_seqn,
                'Volume Total': volume_total,
                'NoP Total': nop_total
            })
    if not result_list:
        logger.error(f"Required data not found for SUPI: {ue_supi}")
        raise ValueError(f"Required data not found for SUPI: {ue_supi}")

    logger.info(f"Found {len(result_list)} records with non-zero traffic for SUPI: {ue_supi}")
    return result_list

def get_iperf3_transfer_size(results):
    last_line = results.split("\n")[-4]
    size = float(last_line.split()[4])
    unit = last_line.split()[5]
    if unit in 'GBytes':
        size = size * 1024 * 1024 * 1024
    if unit in 'MBytes':
        size = size * 1024 * 1024
    elif unit in 'KBytes':
        size = size * 1024
    return size

def extract_info_by_seid_and_urseqn(logs, target_seid, target_ur_seqn):
    log_lines = logs.splitlines()
    for i, line in enumerate(log_lines):
        clean_line = ' '.join(line.split()[4:])
        if f"SEID -> {target_seid}" in clean_line:
            if i + 1 < len(log_lines):
                next_line_clean = ' '.join(log_lines[i + 1].split()[4:])
                if f"UR-SEQN -> {target_ur_seqn}" in next_line_clean:
                    dictionary = {
                        clean_line.split(' -> ')[0]: clean_line.split(' -> ')[1],
                        next_line_clean.split(' -> ')[0]: next_line_clean.split(' -> ')[1]
                    }
                    for j in range(i + 2, i + 11):
                        if j < len(log_lines):
                            line_clean = ' '.join(log_lines[j].split()[4:])
                            if ' -> ' in line_clean:
                                key, value = line_clean.split(' -> ')
                                dictionary[key.strip()] = value.strip()
                    return dictionary
    raise ValueError("No log data available matching the specified SEID and UR-SEQN.")

def Check_ue_traffic_notification(iperf_results, imsi):
    try:
        logs = subprocess.check_output(['docker', 'logs', 'oai-smf'], text=True)
        traffic_iperf_results = get_iperf3_transfer_size(iperf_results)
        # skew between iperf3 results and the results reported by SMF logs
        tolerance = 0.3
        min_val = traffic_iperf_results * (1 - tolerance)
        max_val = traffic_iperf_results * (1 + tolerance)
        callback_data = get_traffic_data_from_handler(imsi)
        iperf_mismatch = False
        handler_mismatch = False
        total_traffic_from_logs = 0
        for data in callback_data:
            smf_traffic_data = extract_info_by_seid_and_urseqn(logs, data['SEID'], data['UR-SEQN'])
            total_traffic_from_logs += int(smf_traffic_data['Volume Total'])
            if int(smf_traffic_data['NoP Total']) != int(data['NoP Total']) or int(smf_traffic_data['Volume Total']) != int(data['Volume Total']):
                logger.error(f"Traffic data mismatch between SMF logs and handler collection for SUPI: {imsi}, Log NoP Total: {smf_traffic_data['NoP Total']}, Callback NoP Total: {int(data['NoP Total'] )}, Logs Volume Total: {smf_traffic_data['Volume Total']}, Callback Volume Total: {data['Volume Total']}")
                handler_mismatch = True
        if not (min_val <= total_traffic_from_logs <= max_val):
            logger.error(f"Total traffic from SMF logs does not match iPerf results within 10% tolerance for SUPI: {imsi}, Total traffic from logs: {total_traffic_from_logs}, Iperf Traffic:{traffic_iperf_results}")
            iperf_mismatch = True
        if handler_mismatch or iperf_mismatch:
            raise Exception(f"Traffic data mismatch for SUPI: {imsi}")
        logger.info(f"SMF Traffic data matches both iPerf results and handler collection for SUPI: {imsi} \n Log NoP Total: {smf_traffic_data['NoP Total']}, Callback NoP Total: {int(data['NoP Total'] )}, Logs Volume Total: {smf_traffic_data['Volume Total']}, Callback Volume Total: {data['Volume Total']}\n iPerf results within 10% tolerance for SUPI: {imsi}, Total traffic from logs: {total_traffic_from_logs}, Iperf Traffic:{traffic_iperf_results}")
    except Exception as e:
        logger.error(f"Failed to check traffic data: {e}")
        raise e

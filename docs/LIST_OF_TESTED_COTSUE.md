<table style="border-collapse: collapse; border: none;">
  <tr style="border-collapse: collapse; border: none;">
    <td style="border-collapse: collapse; border: none;">
      <a href="http://www.openairinterface.org/">
         <img src="./images/oai_final_logo.png" alt="" border=3 height=50 width=150>
         </img>
      </a>
    </td>
    <td style="border-collapse: collapse; border: none; vertical-align: center;">
      <b><font size = "5">List of COTS UEs Tested with OAI</font></b>
    </td>
  </tr>
</table>



|Phone                 |Android Version                                           |PLMN |Remark         |
|----------------------|----------------------------------------------------------|-----|---------------|
|Pixel 5               |11, RQ1C.210205.006, Feb 2021, Google Fi, T-Mobile, Sprint|00101|NA             |
|Pixel 6               |12                                                        |00101|NA             |
|Pixel 6               |13                                                        |00101|Check the notes|
|Pixel 7               |13/14                                                     |00101|Check the notes|
|Huawei P40 and P40 Pro|                                                          |50501|Requires IMS   |
|OnePlus 8             |11 Oxygen OS 11.0.2.2.IN21AA                              |00101|Disable VoLTE  |
|OnePlus 9             |                                                          |00101|Disable VoLTE  |
|OnePlus Nord (ac2003) |12                                                        |00101|NA             |
|Oppo Reno7 Pro        |11 and 12                                                 |00101|NA             |
|iPhone 14 and 14 Pro  |iOS 16.2 +                                                |00101|Requires IMS   |
|iPhone 15 and 15 Pro  |iOS 17.2 +                                                |00101|Requires IMS   |
|Quectel               |RM500Q-GL, RM520-GL, RM502Q-AE, RM500U-CN                 |     |NA             |
|Simcom                |SIMCOM_SIM8200EA-M2                                       |     |NA             |
|Fritzbox 6850         |                                                          |     |NA             |

**Sim Cards**

- Opencells
- Symocom SJS1 and SJA2

**Note**:

1. For Android 13+
  - Dial `*#*#0702#*#*`
  - Search for `NR_TIMER_WAIT_IMS_REGISTRATION` change the value from 180 to `-1` (Infinite timeout)
  - Search for `SUPPORT_IMS_NR_REGISTRATION_TIMER` change the value from default `1` to `0`
2. To force an android phone to `NR ONLY` dial `*#*#4636#*#*` you can also check phone network stats
3. Some phones use TCP for SIP and some UDP. You need to configure the IMS properly

**Known Issues**

1. We have issues with Anritsu Test UICC TM P0551A sim cards because they sent concealed SUCI which is not yet implemented.

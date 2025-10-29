# OpenAirInterface CN5G Documentation Overview

This section provides general guidelines and best practices for maintaining and contributing to the documentation of the OAI CN5G project.

---

## License

This project is distributed under the **OAI Public License V1.1**.  
For more details, please refer to the [OAI Website](https://openairinterface.org/legal/oai-license-model/).


---

## 5G CN Implementation by OAI Community

`OPENAIR-CN-5G`, an implementation of the 3GPP specifications for the 5G Core Network (CN) currently includes the following network functions, each maintained in its own repository:

* **Access and Mobility Management Function (AMF)** – [oai-cn5g-amf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-amf)
* **Authentication Server Function (AUSF)** – [oai-cn5g-ausf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-ausf)
* **Location Management Function (LMF)** – [oai-cn5g-lmf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-lmf)
* **Network Exposure Function (NEF)** – [oai-cn5g-nef](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-nef)
* **Network Repository Function (NRF)** – [oai-cn5g-nrf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-nrf)
* **Network Slicing Selection Function (NSSF)** – [oai-cn5g-nssf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-nssf)
* **Policy Control Function (PCF)** – [oai-cn5g-pcf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-pcf)
* **Session Management Function (SMF)** – [oai-cn5g-smf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-smf)
* **Unified Data Management (UDM)** – [oai-cn5g-udm](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-udm)
* **Unified Data Repository (UDR)** – [oai-cn5g-udr](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-udr)
* **User Plane Function (UPF)** with two variants:
    * Simple implementation (with eBPF option) – [oai-cn5g-upf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-upf)
    * VPP-based implementation – [oai-cn5g-upf-vpp](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-upf-vpp)
* **Unstructured Data Storage Function (UDSF)** – [oai-cn5g-udsf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-udsf)
* **Network Data Analytics Function (NWDAF)** – [oai-cn5g-nwdaf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-nwdaf)


> Note: Some repositories are currently private but will be released soon.

Any merge request or push to the `develop` branch in a network function repository (e.g., `oai-cn5g-amf`) automatically triggers the CI pipeline via GitLab webhooks.

View the pipeline status here: [OAI 5G Core Network Jenkins](https://jenkins-oai.eurecom.fr/view/5G%20Core%20Network/)


---

## Documentation Contribution Guidelines

When opening a **merge request** for documentation updates:

* The **target branch** must be **`develop`**.
* The **`documentation` label** must be added when creating the merge request.
* If you are working on a feature branch, make sure to regularly **`rebase`** it with **`develop`** to stay up to date and avoid conflicts. 

### Folder Structure and File Organization

To maintain a clean, consistent, and well-organized documentation layout, please follow the structure below.

#### **Images and Diagrams**

* Store all image files under the dedicated folder:

  ```
  docs/images/
  ```
* **Do not** place images directly under the `docs/` directory.

  ❌ Incorrect: `docs/amf.png`

  ✅ Correct: `docs/images/amf.png`

Supported image file types are `.png`, `.jpg`/`.jpeg`, `.svg`, `webp`, or `.gif`.

#### **Results, Logs, and PCAPs**

* Store all result-related files (such as logs, PCAPs, and similar data) under:

  ```
  docs/results/
  ```
* Always update file paths in Markdown accordingly when adding or modifying image or result links.

---

### Use Proper Markdown — Avoid Inline HTML

Always use **standard Markdown syntax** and **avoid inline HTML**.
Use pure Markdown for **titles, images, tables, and formatting** to ensure portability and compatibility across Markdown renderers.

#### Examples

##### **Titles**

Do **not** use HTML tables or inline styles for headers.

❌ **Incorrect:**

```html
<table style="border-collapse: collapse; border: none;">
  <tr>
    <td>
      <a href="http://www.openairinterface.org/">
        <img src="images/oai_final_logo.png" alt="" height=50 width=150>
      </a>
    </td>
    <td>
      <b><font size="5">OpenAirInterface 5G Core Network Deployment: Building Container Images</font></b>
    </td>
  </tr>
</table>
```

✅ **Correct (Markdown):**

```markdown
# OpenAirInterface 5G Core Network Deployment: Building Container Images
```

##### **Figures**

Do **not** use HTML `<figure>` or `<figcaption>` elements for images.

❌ **Incorrect:**

```html
<figure>
  <img src="./images/5gcn_eBPF_upf.png" alt="UPF architecture using eBPF technology" width="900" height="600" />
  <figcaption><b><font size="5">Figure 1: UPF Architecture: eBPF XDP based</font></b></figcaption>
</figure>
```

✅ **Correct (Markdown):**

```markdown
![This is the UPF architecture using the eBPF technology. The architecture is designed in two layers: user and kernel space layers.](images/5gcn_eBPF_upf.png)

**Figure 1: UPF Architecture – eBPF XDP based**
```

---

### Headings

* Only **one** top-level heading (`# H1`) should exist per document.
* Use subsequent heading levels (`##` to `######`) for subheadings.
* Do **not** add trailing `#` symbols after headings.

❌ Incorrect:

```
# OpenAirInterface 5G Core Network
# Workflow and Versioning #
## Manage your own branch
## Merge Requests
```

✅ Correct:

```
# OpenAirInterface 5G Core Network
## Workflow and Versioning
### Manage your own branch
### Merge Requests
```

---

### Quoting Code, Files, and Commands

Use single backticks (`` ` ``) to reference code, files, or commands **inline**.

**Examples:**

```markdown
* Use the `--verbose` option to see each command’s execution.  
* We configured a new IP range by adding the `/etc/docker/daemon.json` file.  
```

For **multi-line code blocks**, use triple backticks with a language identifier for syntax highlighting.

````bash
```bash
docker --version
docker images
docker ps -a
docker system prune -a
```
````

> **Note:** To make commands copy-friendly, **avoid using `$` signs** and use plain commands.

Also ensure:

* No extra whitespace before backticks.
* The appropriate language (e.g., `bash`, `python`, `yaml`, `json`, etc.) is specified for syntax highlighting.

#### Collapsible Sections

You can create collapsible sections that expand when clicked — useful for hiding long outputs, logs, or optional details.
This feature helps keep your documentation concise while still providing extra information when needed.

**Example:**

````markdown
<details>
<summary>Expected Output</summary>

```bash
Docker version 28.0.4, build b8034c0
```

</details>
````

**Rendered Output:**

<details>
<summary>Expected Output</summary>

```bash
Docker version 28.0.4, build b8034c0
```

</details>

---

### Links

Create inline links using standard Markdown syntax:

✅ **Correct:**

```markdown
You can pull the Docker images from [OAI DockerHub](https://hub.docker.com/u/oaisoftwarealliance).
```

❌ **Incorrect:**

```markdown
You can pull the Docker images from https://hub.docker.com/u/oaisoftwarealliance.
```

---

### Relative Links

Use **relative links** for navigation within the repository to keep references portable.

**Example:**

```bash
.
├── fed
│   ├── BUILD_IMAGES.md
│   ├── FEATURE_SET.md
│   └── network-functions
│       └── amf.md
├── images
│   └── logo.png
└── README.md

```

**Referencing an Image (from `BUILD_IMAGES.md`):**

```markdown
![OAI Logo](../images/logo.png)
```

**Linking to Another File (`FEATURE_SET.md`) in the same directory:**

```markdown
Feature set of this project is defined in the file [FEATURE_SET.md](FEATURE_SET.md).
```

**Linking from a Subfolder to a File One Level Up (from `amf.md` to `BUILD_IMAGES.md`):**

```markdown
Refer to the build instructions in [BUILD_IMAGES.md](../BUILD_IMAGES.md).
```
**Linking from a Subfolder to a File Two Levels Up (from `amf.md` to `README.md`):**

```markdown
For the main documentation, see [README.md](../../README.md).
```

---

### Section Links

You can create links that point directly to specific sections within your Markdown file.
This is useful for easy navigation, especially in long documents.

**Example:**

```markdown
# OpenAirInterface

## 5G Core Network (CN5G)

### Building Container Images

Each 5G Network Function (NF) source code is maintained in its own repository.

### Access and Mobility Management Function (AMF)

You can build the AMF image by following the steps in the [Building Container Images](#building-container-images) section.
```

In the above example, clicking **“Building Container Images”** will take you directly to that section.

---

### Quoting Text

Use the `>` character to create callout blocks for **notes**, **warnings**, or **cautions**.
This helps highlight important information and improves readability.

**Example:**

```markdown
> **Note:** When creating a merge request, make sure to select `develop` as the target branch.
```

**Rendered Output:**

> **Note:** When creating a merge request, make sure to select `develop` as the target branch.


---


### Tables and Lists in Markdown

Use **Markdown syntax only** for tables and lists. Avoid HTML tags for consistency.

#### **Tables**

**Example:**

```markdown
| Parameter | Description | Example |
|------------|--------------|----------|
| `IMAGE_TAG` | Docker image version tag | `develop` |
| `NF` | Network function | `oai-amf` |
```

**Output:**

| Parameter   | Description                 | Example          |
| ----------- | --------------------------- | ---------------- |
| `IMAGE_TAG` | Docker image version tag    | `develop`         |
| `NF`   | Network function | `oai-amf` |

---

#### **Lists**

**Unordered:**

```markdown
* AMF – Access and Mobility Management Function  
* SMF – Session Management Function  
* UPF – User Plane Function
```

**Ordered:**

```markdown
1. Clone the repository  
2. Build the image  
3. Verify with `docker images`
```

---


### Spacing and Line Length

* Maintain **consistent spacing** between paragraphs and sections.  
* Use **line breaks** to separate logical blocks of text.  
* Keep **paragraphs concise**, ideally 4-8 lines each. 
* **Organize content into lists or key points** wherever possible to enhance clarity.
* Limit lines to **80–100 characters** to improve readability.
* Use visual separators like `---` to clearly indicate **section breaks** when needed.    

---
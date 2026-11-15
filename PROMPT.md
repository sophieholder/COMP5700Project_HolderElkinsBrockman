# PROMPT.md

Prompts used in Task-1 (Extractor) to identify key data elements (KDEs) and their requirements in two CIS Docker Benchmark documents. The target LLM is **Gemma-3-1B**. `<DOCUMENT 1 TEXT>` / `<DOCUMENT 2 TEXT>` and the document names are filled in at runtime. The document text is the compact recommendation list taken from each PDF's "Appendix: Summary Table" (see `src/pdf_utils.py`), because the full PDFs are far too long for a 1B model. These prompts are generated from the templates in `src/prompts.py`.

## Zero-shot

Task description, KDE definition, rules and output format only. No examples.

````text
You are a security compliance analyst. Read the two CIS Docker Benchmark excerpts below and identify the key data elements (KDEs) and the requirements attached to each KDE.

A key data element (KDE) is a distinct configuration target, object, or component
that the security benchmark gives requirements about (for example: Docker daemon
configuration, container images and build files, container runtime, host
configuration, Docker Swarm). A single KDE can map to several requirements. A
requirement is a concrete recommendation that applies to that KDE (for example:
"Ensure that a user for the container has been created"; "Ensure that COPY is used
instead of ADD in Dockerfiles").

The documents are lists of numbered recommendations such as
"4.1 Ensure that a user for the container has been created (Manual)", grouped under
section headings that start with "##". Write each requirement as the recommendation
title, without its number and without the (Manual) / (Automated) label.

Rules:
- Use only information that appears in the documents.
- Group requirements under the KDE they belong to.
- Do not invent elements or requirements.

Return ONLY valid YAML in exactly this structure (no commentary, no code fences):

element1:
  name: <short name of the key data element>
  requirements:
    - <requirement 1>
    - <requirement 2>
element2:
  name: <short name of the key data element>
  requirements:
    - <requirement 1>

### DOCUMENT 1: <doc-1 name>
<DOCUMENT 1 TEXT>

### DOCUMENT 2: <doc-2 name>
<DOCUMENT 2 TEXT>

### YAML OUTPUT
````

## Few-shot

Same instructions plus three worked examples using real CIS Docker Benchmark recommendations.

````text
You are a security compliance analyst. Identify the key data elements (KDEs) and the requirements attached to each KDE in CIS Docker Benchmark documents.

A key data element (KDE) is a distinct configuration target, object, or component
that the security benchmark gives requirements about (for example: Docker daemon
configuration, container images and build files, container runtime, host
configuration, Docker Swarm). A single KDE can map to several requirements. A
requirement is a concrete recommendation that applies to that KDE (for example:
"Ensure that a user for the container has been created"; "Ensure that COPY is used
instead of ADD in Dockerfiles").

The documents are lists of numbered recommendations such as
"4.1 Ensure that a user for the container has been created (Manual)", grouped under
section headings that start with "##". Write each requirement as the recommendation
title, without its number and without the (Manual) / (Automated) label.

Return ONLY valid YAML in exactly this structure (no commentary, no code fences):

element1:
  name: <short name of the key data element>
  requirements:
    - <requirement 1>
    - <requirement 2>
element2:
  name: <short name of the key data element>
  requirements:
    - <requirement 1>

Here are worked examples of the task:

### EXAMPLE 1
Document excerpt:
## 4 Container Images and Build File Configuration
4.1 Ensure that a user for the container has been created (Manual)
4.6 Ensure that HEALTHCHECK instructions have been added to container images (Manual)
4.7 Ensure update instructions are not used alone in Dockerfiles (Manual)
4.9 Ensure that COPY is used instead of ADD in Dockerfiles (Manual)

YAML output:
element1:
  name: Container images and build files
  requirements:
    - Ensure that a user for the container has been created
    - Ensure that HEALTHCHECK instructions have been added to container images
    - Ensure update instructions are not used alone in Dockerfiles
    - Ensure that COPY is used instead of ADD in Dockerfiles

### EXAMPLE 2
Document excerpt:
## 2 Docker daemon configuration
2.2 Ensure network traffic is restricted between containers on the default bridge (Manual)
2.3 Ensure the logging level is set to 'info' (Manual)
2.5 Ensure insecure registries are not used (Manual)
2.6 Ensure aufs storage driver is not used (Manual)

YAML output:
element1:
  name: Docker daemon
  requirements:
    - Ensure network traffic is restricted between containers on the default bridge
    - Ensure the logging level is set to 'info'
    - Ensure insecure registries are not used
    - Ensure aufs storage driver is not used

### EXAMPLE 3
Document excerpt:
## 5 Container Runtime Configuration
5.5 Ensure that privileged containers are not used (Manual)
5.10 Ensure that the host's network namespace is not shared (Manual)
5.11 Ensure that the memory usage for containers is limited (Manual)

YAML output:
element1:
  name: Container runtime
  requirements:
    - Ensure that privileged containers are not used
    - Ensure that the host's network namespace is not shared
    - Ensure that the memory usage for containers is limited

Now do the same for the two real documents below. Use only information in the documents.

### DOCUMENT 1: <doc-1 name>
<DOCUMENT 1 TEXT>

### DOCUMENT 2: <doc-2 name>
<DOCUMENT 2 TEXT>

### YAML OUTPUT
````

## Chain-of-thought

Explicit five-step reasoning procedure, then the final YAML.

````text
You are a security compliance analyst. Identify the key data elements (KDEs) and their requirements in the two CIS Docker Benchmark excerpts below. Think step by step.

A key data element (KDE) is a distinct configuration target, object, or component
that the security benchmark gives requirements about (for example: Docker daemon
configuration, container images and build files, container runtime, host
configuration, Docker Swarm). A single KDE can map to several requirements. A
requirement is a concrete recommendation that applies to that KDE (for example:
"Ensure that a user for the container has been created"; "Ensure that COPY is used
instead of ADD in Dockerfiles").

The documents are lists of numbered recommendations such as
"4.1 Ensure that a user for the container has been created (Manual)", grouped under
section headings that start with "##". Write each requirement as the recommendation
title, without its number and without the (Manual) / (Automated) label.

Work through these steps in order:
Step 1: Read each document and list every numbered recommendation (for example "4.1 Ensure ...") together with its title.
Step 2: For each recommendation, decide which component it is about (Docker daemon, container images and build files, container runtime, host configuration, and so on). That component is the KDE.
Step 3: Group recommendations that share the same KDE. One KDE may have many requirements.
Step 4: Give each KDE a short, clear name and write each requirement as the recommendation title.
Step 5: Re-check that every KDE and requirement came from the documents and nothing was invented.

Write your reasoning briefly under the heading REASONING. Then write the final answer under the heading FINAL YAML.

Return ONLY valid YAML in exactly this structure (no commentary, no code fences):

element1:
  name: <short name of the key data element>
  requirements:
    - <requirement 1>
    - <requirement 2>
element2:
  name: <short name of the key data element>
  requirements:
    - <requirement 1>

### DOCUMENT 1: <doc-1 name>
<DOCUMENT 1 TEXT>

### DOCUMENT 2: <doc-2 name>
<DOCUMENT 2 TEXT>

### REASONING
````

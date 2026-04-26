# Echo Protocol

A web tool for generating Beckman Echo liquid handler protocols. Generate CSV transfer files for your experiments without writing code.

## What is this?

The Beckman Echo is a liquid handling robot that transfers nanoliters of fluid between plates. This tool helps you:
- Set up experiments using premade plate layouts, or create new ones
- Define sample concentrations and volumes
- Download CSV files ready for the Echo robot

No programming required - just fill out a web form and download your protocol.

## Quick Start

### 1. Pull the Docker Image

```bash
docker pull ghcr.io/atmollohan/echo:latest
```

### 2. Run the App

```bash
docker run -p 8501:8501 ghcr.io/atmollohan/echo:latest
```

### 3. Open in Browser

Go to: **http://localhost:8501**

You'll see the web interface with a form to configure your experiment.

---

## How to Use the App

### Step 1: Choose Your Starting Point

- **Use a premade plate** - Start with an existing plate layout from the examples
- **Create a new plate** - Define your own source plate from scratch

### Step 2: Fill Out the Form

Enter your experiment parameters:
- Experiment name
- Number of doses/concentrations
- Sample names
- Volumes (in nanoliters)

### Step 3: Generate the Protocol

Click **Generate Protocol** to create your CSV files.

### Step 4: Download

Review the generated plates and download:
- Source plate CSV (what goes in each well of the source plate)
- Transfer protocol CSV (what the robot transfers)

---

## Example Workflows

### Using a Premade Plate

1. Select "Use a premade plate"
2. Choose a reference plate (e.g., Library Plate A)
3. The form autofills with example values
4. Adjust doses, volumes, or samples as needed
5. Generate and download

### Creating a New Plate

1. Select "Create a new plate"
2. Enter your experiment name
3. Specify number of samples and doses
4. Set volumes for cell extract and antigen
5. Generate and download

---

## Mounting Custom Files (Optional)

If you want to use your own notebooks or data:

```bash
docker run -p 8501:8501 \
  -v /path/to/your/notebooks:/workspace/notebooks \
  -v /path/to/your/data:/workspace/data \
  -e ECHO_NOTEBOOKS_DIR=/workspace/notebooks \
  -e ECHO_DATA_DIR=/workspace/data \
  ghcr.io/atmollohan/echo:latest
```

---

## System Requirements

- Docker installed on your computer
- Any computer (works on Intel Mac, Apple Silicon Mac, Linux, Raspberry Pi)

The Docker image pulls the correct architecture automatically.

---

## Troubleshooting

### Port 8501 is in use

```bash
# Use a different port
docker run -p 8502:8501 ghcr.io/atmollohan/echo:latest
```

### Can't access localhost:8501

- Make sure Docker is running
- Check the container is running: `docker ps`
- Try http://127.0.0.1:8501 instead

---

## Need Help?

This tool is designed for lab scientists who want to generate Echo protocols without coding. If you have questions or run into issues, open an issue on GitHub: https://github.com/atmollohan/echo/issues

---

## License

MIT
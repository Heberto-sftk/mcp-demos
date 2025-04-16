 🧪 mcp-demos

A demo project for mcp servers.
## 🚀 Getting Started

Follow these steps to set up and run the project.

### 1️⃣ Create a Virtual Environment

It's recommended to use a virtual environment to manage dependencies:

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 2️⃣ Install Requirements

Install the required packages:

```bash
pip install -r requirements.txt
```

### 3️⃣ Run the MCP Server

You can start the server in one of two modes:

#### ▶️ Normal Mode

```bash
mcp run <file_name>
```

#### 🛠 Developer Mode

```bash
mcp dev <file_name>
```

#### 🛠 Connection Mode

```bash
python <file_name>
```

Replace `<file_name>` with the appropriate script or module name you want to run.

---

### 4 Run the fasstapi connection

```bash
func host start
```

## 📁 Project Structure

```
mcp-demos/
│
├── requirements.txt
├── <your_python_files>.py
└── README.md
```

---

## 🧰 Requirements

Make sure you have Python 3.7+ installed.

---

## 📬 Feedback

Feel free to open issues or contribute to improve the demos!

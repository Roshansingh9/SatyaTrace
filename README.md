# SatyaTrace - WhatsApp AI Tool for Message Analysis

SatyaTrace is a WhatsApp AI tool designed to analyze suspicious messages and provide information forensics. This project leverages FastAPI for building a webhook that receives messages from WhatsApp and utilizes AI techniques to analyze the content for potential claims and misinformation.

## Project Structure

```
SatyaTrace
├── src
│   ├── main.py               # Entry point of the application
│   ├── ai
│   │   └── analyzer.py       # Logic for analyzing messages
│   ├── models
│   │   └── message.py        # Data model for WhatsApp messages
│   ├── routes
│   │   └── webhook.py        # Webhook route for incoming messages
│   └── utils
│       └── forensics.py      # Utility functions for information forensics
├── requirements.txt          # Project dependencies
├── README.md                 # Project documentation
└── .gitignore                # Files to ignore by Git
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd SatyaTrace
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. **Install the required dependencies:**
   ```
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application:**
   ```
   uvicorn src.main:app --reload
   ```

2. **Access the API:**
   Open your browser and navigate to `http://127.0.0.1:8000/` to see the welcome message.

3. **Webhook Integration:**
   Set up your WhatsApp API to send messages to the `/webhook` endpoint of your application.

## Features

- **Message Analysis:** Analyze incoming WhatsApp messages for suspicious content.
- **Claim Verification:** Extract and verify claims made in the messages.
- **Information Forensics:** Track the origin and spread of messages.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or features you'd like to add.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
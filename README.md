# A Blockchain based Certificate verification system in Python, Ganache, Js and Solidity

## Introduction

This project provides a Blockchain-based solution for generating and verifying digital certificates. The certificate information (Registration_No, candidate_name, course_name, Institution, ipfs_hash) is stored on the blockchain. First, the certificate PDF is generated and stored onto IPFS using the Pinata service. Then, the IPFS hash obtained is stored on the blockchain along with other information.

The system comprises of 2 main entities:
- **Institute**: Responsible for generating and issuing certificates. Has the functionality to generate and view certificates.
- **Verifier**: Responsible for verifying certificates. Has the functionality to verify certificates by either uploading a certificate PDF or by inputting the certificate ID.

---

## Features

- **Smart Contract:** Utilizes a Solidity smart contract to manage and store certificate details on the Ethereum blockchain.
- **IPFS Integration:** Stores certificate PDFs on IPFS via Pinata for decentralized and secure file storage.
- **Firebase Authentication:** Uses Firebase for authentication.
- **Streamlit App:** Provides a user-friendly interface for generating and verifying certificates.

---

## Getting Started

Clone the repository using the command:
```sh
git clone https://github.com/Hacx2/Blockchain-certificate-verification-system.git
```
You can run the project either through:
- [Local Setup](#local-setup)(Recommended)

---

## Local Setup

### Prerequisites

- **Node version >= 21.0.0**  
  Truffle requires node version 16 or higher. The node version on my machine on which I tested this project was 21.0.0. You can try a lower node version (>=16.0).

- **Python version >= 3.9.10**  
  Python version 3.9.10 or higher is recommended but other versions may also work.

- **Globally installed packages for Truffle and Ganache-cli to prevent installing again**  
  ```sh
  npm install -g truffle
  ```
  ```sh
  npm install -g ganache-cli
  ```

- **Python packages**  
  In the project's root directory, execute the command:
  ```sh
  pip install -r application/requirements.txt
  ```
  It is recommended to create a virtual environment and then install the requirements and run the Streamlit application in that virtual environment.

- **Firebase project setup**  
  Create a project on [Firebase Console](https://console.firebase.google.com/). This will be used to set up an authentication service in the project. Enable email/password sign-in method under Authentication in the Build section.
  Go to project settings. Add a new app. Note the following details in a .env file inside the project's root directory.
  ```sh
  FIREBASE_API_KEY
  FIREBASE_AUTH_DOMAIN
  FIREBASE_DATABASE_URL (Set this to "")
  FIREBASE_PROJECT_ID
  FIREBASE_STORAGE_BUCKET
  FIREBASE_MESSAGING_SENDER_ID
  FIREBASE_APP_ID
  ```

- **Pinata account setup**  
  Create an account on [Pinata](https://app.pinata.cloud/). Go to the API keys section and generate a new key. Note the API key and secret key in the .env file.

- **.env file**  
  Finally, your .env file should contain the following things:
  ```sh
  PINATA_API_KEY = "<Your Pinata API key>"
  PINATA_API_SECRET = "<Your Pinata Secret Key>"
  FIREBASE_API_KEY = "<Your Firebase API key>"
  FIREBASE_AUTH_DOMAIN = "<Your Firebase auth domain>"
  FIREBASE_DATABASE_URL = ""
  FIREBASE_PROJECT_ID = "<Your Firebase project id>"
  FIREBASE_STORAGE_BUCKET = "<Your Firebase Storage Bucket>"
  FIREBASE_MESSAGING_SENDER_ID = "<Your Firebase messaging sender id>"
  FIREBASE_APP_ID = "<Your Firebase app id>"
  institute_email = "institution@gmail.com" # Feel free to modify this
  institute_password = "desiredpassword" # Feel free to modify this
  ```
  Note: This institute email and password in the .env file will be used to log in as Institute inside the app.

### Running the project
**If using cli ganache ensure the cli runs**
 ```sh
  ganache-cli
  ```
  **must run on a separate terminal**
  
1. Use local ganache app/ Use CLI ganache any of your choice(Add the truffle-config.js file to a new workspace)
    ```sh
    npm install -g truffle
    ```

2. Open a new terminal in the project's root directory and execute the following command to compile and deploy the smart contracts.
    ```sh
    truffle migrate
    ```

3. Create virtual environment python to run the project first change the working directory to the application directory inside the project's root directory.
    ```sh
    cd <projectpath>
    virtualenv myenv
    .\myenv\Scripts\Activate
    cd Application
    ```

4. Install dependancies first. 
    ```sh
    pip install -r application/requirements.txt
    ```

5. Launch the Streamlit app.
    ```sh
    streamlit run app.py
    ```

6. You can now view the app on your browser running on [localhost:8501](http://localhost:8501).

7. To stop the application, press Ctrl+C.

---

## Application Screenshots

![Home page](/BCV/Homepage.png)
<p align="center"><em>Home Page</em></p>
<br></br>

![Institute Login page](/BCV/Institute%20login%20page.png)
<p align="center"><em>Login Page</em></p>
<br></br>

![Single Certificate generation](/BCV/Single%20cert%20generation.jpg)
<p align="center"><em>Single Certificate generate</em></p>
<br></br>

![Bulk Certificate generation](/BCV/bulk%20generation.jpg)
<p align="center"><em>Bulk Certificate generation</em></p>
<br></br>

![Manage Institution page](/BCV/manage%20institution.jpg)
<p align="center"><em>Manage Institution page</em></p>
<br></br>

![Revoke Certificate page](/BCV/revoke%20certificate%20page.jpg)
<p align="center"><em>Revoke Certificate page</em></p>
<br></br>

![Verifying Certificate page](/BCV/verifying.png)
<p align="center"><em>Verifying Certificate page</em></p>
<br></br>
---


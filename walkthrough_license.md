# RMS Licensing Walkthrough

I have successfully implemented the entire licensing suite based on our approved plan! We now have robust security to prevent unauthorized access while easily enforcing your 100-user limit.

## What Was Added

1. **`hardware_extractor.py`**: A tiny Python script the client runs on their physical server to generate a secure `MACH-XXXX` code.
2. **`license_generator.py`**: Your offline Admin script that prompts you for details (Max Users, Expiry, Binding Type) and generates the RSA-signed `license.key`.
3. **`license_validator.py`**: A utility script meant to be imported by the actual RMS Backend (and currently used by the Admin Tool) to securely parse and validate the JWT license file against tampering.
4. **Excel Upload Limit Integration**: The Admin Tool (`unified_upload.py`) now dynamically reads the `license.key` file. When you upload a Master Excel sheet, it calculates `current_users + incoming_users`. If it exceeds 100, it safely inserts up to the limit and displays a yellow warning that the remaining users were ignored.

## How to use it (The Vendor Flow)

When you onboard a new client:

1. **Generate the Keys**: 
   Open your terminal in the Admin Tool directory and run:
   ```bash
   python utils/license_generator.py
   ```
   Follow the prompts to generate a license. It will automatically create an RSA Keypair if you don't have one.

2. **Delivery**: 
   Send the resulting `license.key` and the `rms_public.pem` files to the client to place in their server's root folder. **Never share the `vendor_private.pem` file.**

3. **Try it out**:
   Refresh your Streamlit dashboard. It will now actively look for the `license.key` file. If the file is missing or invalid, it will enforce a strict `max_users = 0` limit and refuse to upload *any* users! Once you generate a valid key with 100 max users, the upload will work normally.

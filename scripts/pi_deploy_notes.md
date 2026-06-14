# Raspberry Pi Deployment Notes

These notes are the intended implementation path for the field appliance.

1. Rotate the temporary setup password before field use.
2. Install Python 3.11+, `llama.cpp`, and the dependencies in `requirements.txt`.
3. Copy this repository to the Pi.
4. Run `python app.py` for a quick manual test.
5. Install the llama.cpp prebuilt runtime and smoke model:
   - `bash scripts/install_llama_cpp_pi.sh`
6. Add systemd services for:
   - `llama-server`
   - `outbush-ai`
   - optional `kiwix-serve`
   - hotspot/mDNS
7. Configure the access point:
   - SSID: `Outbush-AI`
   - Local URL: `http://outbush.local`
8. Run `python scripts/pi_smoke_test.py http://127.0.0.1:7860` on the Pi.

The app itself must remain useful without the llama.cpp model loaded; deterministic safety fallbacks are intentional.

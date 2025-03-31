import qrcode

# De URL die je wilt omzetten naar een QR-code
url = "https://forms.gle/aF91rZ8Jh3rWEmsNA"

# QR-code object aanmaken
qr = qrcode.QRCode(
    version=1,  # versie van de QR-code, bepaalt de grootte van de code
    error_correction=qrcode.constants.ERROR_CORRECT_L,  # foutcorrectieniveau
    box_size=10,  # grootte van de vakjes in de QR-code
    border=4,  # dikte van de rand
)

# De data (URL) toevoegen aan de QR-code
qr.add_data(url)
qr.make(fit=True)

# QR-code afbeelding genereren
img = qr.make_image(fill='black', back_color='white')

# Opslaan van de afbeelding
img.save("qrcode_example.png")

print("QR-code is gegenereerd en opgeslagen als qrcode_example.png")

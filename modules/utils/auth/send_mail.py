import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import db_async, db_sync, settings
from bunnet import init_bunnet
from models.otp import OtpCode
from schema.otp import CreateOtpCode
import random

def generate_otp(length: int = 6) -> str:
    """Sinh mã OTP gồm length chữ số"""
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


async def save_otp_to_db(email: str, otp: str):
    """Lưu OTP vào DB"""
    init_bunnet(database=db_sync, document_models=[OtpCode])
    otp_doc = OtpCode(email=email, otp=otp)
    await otp_doc.insert()
    return otp_doc


def send_otp_email(to_email, otp_code):
    from_email = "luongthaison2k4@gmail.com"
    app_password = "tgxb kvxb gorx fixx"  # mật khẩu ứng dụng

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Mã xác nhận đăng ký"
    body = f"Mã xác nhận của bạn là: {otp_code}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, app_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print("Email OTP đã gửi thành công!")
        return True
    except Exception as e:
        print("Gửi email thất bại:", e)
        return False


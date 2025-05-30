import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import docker
import os
import subprocess
import uuid
import shutil

# توکن ربات تلگرام
TOKEN = "7530258287:AAEQzSqEYvU9pOM8UfqSPhW6hDs9nbqR-Sw"  # توکن را از BotFather دریافت کنید

# تنظیمات Docker برای زبان‌های مختلف
LANGUAGE_CONFIGS = {
    "python": {
        "image": "python:3.9-slim",
        "extension": ".py",
        "run_cmd": "python {file}",
        "package_manager": "pip install {package}"
    },
    "javascript": {
        "image": "node:16",
        "extension": ".js",
        "run_cmd": "node {file}",
        "package_manager": "npm install {package}"
    },
    "java": {
        "image": "openjdk:11",
        "extension": ".java",
        "run_cmd": "javac {file} && java {class_name}",
        "package_manager": "mvn install {package}"
    },
    "cpp": {
        "image": "gcc:latest",
        "extension": ".cpp",
        "run_cmd": "g++ {file} -o output && ./output",
        "package_manager": "apt-get install {package}"
    },
    "go": {
        "image": "golang:latest",
        "extension": ".go",
        "run_cmd": "go run {file}",
        "package_manager": "go get {package}"
    }
}

# مسیر موقت برای ذخیره کدها
TEMP_DIR = "./temp_code"

# اطمینان از وجود دایرکتوری موقت
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# تابع شروع ربات
async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Python", callback_data="python")],
        [InlineKeyboardButton("JavaScript", callback_data="javascript")],
        [InlineKeyboardButton("Java", callback_data="java")],
        [InlineKeyboardButton("C++", callback_data="cpp")],
        [InlineKeyboardButton("Go", callback_data="go")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفاً زبان برنامه‌نویسی را انتخاب کنید:", reply_markup=reply_markup)

# مدیریت انتخاب زبان
async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    language = query.data
    context.user_data["language"] = language
    await query.message.reply_text(f"زبان {language} انتخاب شد. حالا می‌توانید پکیج نصب کنید یا کد خود را ارسال کنید.\n"
                                  f"برای نصب پکیج: /install <نام_پکیج>\n"
                                  f"برای ارسال کد: کد خود را مستقیماً بنویسید.")

# نصب پکیج
async def install_package(update, context):
    if "language" not in context.user_data:
        await update.message.reply_text("لطفاً ابتدا یک زبان انتخاب کنید!")
        return

    language = context.user_data["language"]
    package = " ".join(context.args)
    if not package:
        await update.message.reply_text("لطفاً نام پکیج را وارد کنید!")
        return

    config = LANGUAGE_CONFIGS[language]
    client = docker.from_env()
    container = client.containers.run(
        config["image"],
        command=config["package_manager"].format(package=package),
        volumes={os.path.abspath(TEMP_DIR): {"bind": "/code", "mode": "rw"}},
        working_dir="/code",
        detach=True
    )
    result = container.wait()
    logs = container.logs().decode("utf-8")
    container.remove()

    if result["StatusCode"] == 0:
        await update.message.reply_text(f"پکیج {package} با موفقیت نصب شد:\n{logs}")
    else:
        await update.message.reply_text(f"خطا در نصب پکیج:\n{logs}")

# اجرای کد
async def handle_code(update, context):
    if "language" not in context.user_data:
        await update.message.reply_text("لطفاً ابتدا یک زبان انتخاب کنید!")
        return

    language = context.user_data["language"]
    code = update.message.text
    config = LANGUAGE_CONFIGS[language]

    # ذخیره کد در فایل موقت
    file_id = str(uuid.uuid4())
    file_path = os.path.join(TEMP_DIR, f"{file_id}{config['extension']}")
    with open(file_path, "w") as f:
        f.write(code)

    # برای Java، نیاز به استخراج نام کلاس داریم
    class_name = file_id if language != "java" else get_java_class_name(code)

    client = docker.from_env()
    try:
        container = client.containers.run(
            config["image"],
            command=config["run_cmd"].format(file=f"/code/{file_id}{config['extension']}", class_name=class_name),
            volumes={os.path.abspath(TEMP_DIR): {"bind": "/code", "mode": "rw"}},
            working_dir="/code",
            detach=True,
            mem_limit="512m",  # محدودیت حافظه برای جلوگیری از سوءاستفاده
            cpu_period=100000,
            cpu_quota=50000  # محدودیت CPU
        )
        result = container.wait()
        logs = container.logs().decode("utf-8")
        container.remove()

        if result["StatusCode"] == 0:
            await update.message.reply_text(f"نتیجه اجرا:\n{logs}")
        else:
            await update.message.reply_text(f"خطا در اجرا:\n{logs}")
    except Exception as e:
        await update.message.reply_text(f"خطا: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# استخراج نام کلاس برای Java
def get_java_class_name(code):
    import re
    match = re.search(r"public\s+class\s+(\w+)", code)
    return match.group(1) if match else "Main"

# ساخت اپلیکیشن موبایل (مثال با Flutter)
async def build_app(update, context):
    if "language" not in context.user_data or context.user_data["language"] != "python":
        await update.message.reply_text("ساخت اپلیکیشن فقط با Python و Flutter پشتیبانی می‌شود!")
        return

    code = update.message.text
    app_id = str(uuid.uuid4())
    app_dir = os.path.join(TEMP_DIR, f"flutter_app_{app_id}")
    os.makedirs(app_dir)

    # ایجاد پروژه Flutter ساده
    flutter_code = """
import 'package:flutter/material.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: Text('My App')),
        body: Center(child: Text('Hello from Flutter!')),
      ),
    );
  }
}
"""
    with open(os.path.join(app_dir, "main.dart"), "w") as f:
        f.write(flutter_code)

    client = docker.from_env()
    try:
        container = client.containers.run(
            "flutter:latest",  # فرض بر وجود ایمیج Flutter
            command="flutter build apk",
            volumes={os.path.abspath(app_dir): {"bind": "/app", "mode": "rw"}},
            working_dir="/app",
            detach=True
        )
        result = container.wait()
        logs = container.logs().decode("utf-8")
        container.remove()

        if result["StatusCode"] == 0:
            apk_path = os.path.join(app_dir, "build/app/outputs/flutter-apk/app-release.apk")
            if os.path.exists(apk_path):
                with open(apk_path, "rb") as f:
                    await update.message.reply_document(document=f, filename="app.apk")
            else:
                await update.message.reply_text("فایل APK تولید نشد!")
        else:
            await update.message.reply_text(f"خطا در ساخت اپلیکیشن:\n{logs}")
    except Exception as e:
        await update.message.reply_text(f"خطا: {str(e)}")
    finally:
        if os.path.exists(app_dir):
            shutil.rmtree(app_dir)

# تنظیم ربات
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(CommandHandler("install", install_package))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code))
    app.add_handler(CommandHandler("build_app", build_app))

    app.run_polling()

if __name__ == "__main__":
    main()

import io
import sys
import traceback
import subprocess
from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.helpers.filters import owner_only


@bot.on_message(filters.command(["eval"]) & owner_only)
async def eval_command(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: <code>/eval [python_code]</code>")

    code = message.text.split(None, 1)[1]
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    redirected_output = io.StringIO()
    redirected_error = io.StringIO()
    sys.stdout = redirected_output
    sys.stderr = redirected_error

    exc = None
    try:
        await aexec(code, bot, message)
    except Exception:
        exc = traceback.format_exc()

    sys.stdout = old_stdout
    sys.stderr = old_stderr

    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()

    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success (No Output)"

    if len(evaluation) > 4000:
        evaluation = evaluation[:4000] + "..."

    await message.reply_text(f"<b>Output:</b>\n<pre language=\"python\">{evaluation}</pre>")


async def aexec(code, bot, message):
    exec(
        f"async def __aexec(bot, message): "
        + "".join(f"\n {line}" for line in code.split("\n"))
    )
    return await locals()["__aexec"](bot, message)


@bot.on_message(filters.command(["sh"]) & owner_only)
async def shell_command(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: <code>/sh [command]</code>")

    cmd = message.text.split(None, 1)[1]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    out, err = proc.communicate()

    res = (out or "") + (err or "")
    if not res:
        res = "Done (Return Code 0)"
    if len(res) > 4000:
        res = res[:4000] + "..."

    await message.reply_text(f"<b>Shell Output:</b>\n<pre>{res}</pre>")

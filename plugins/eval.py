import io
import sys
import traceback
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID, COMMAND_PREFIXES

@Client.on_message(filters.command(["eval"], prefixes=COMMAND_PREFIXES) & filters.user(OWNER_ID))
async def eval_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("💻 <b>Usage:</b> <code>/eval [Python code]</code>")

    cmd = message.text.split(maxsplit=1)[1]
    msg = await message.reply_text("⚙️ <i>Evaluating Python code...</i>")

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None

    try:
        # Wrap async code
        compiled = compile(f"async def _eval_func():\n" + "\n".join(f"    {line}" for line in cmd.split("\n")), "<eval>", "exec")
        locs = {"client": client, "message": message, "app": client}
        exec(compiled, globals(), locs)
        func = locs["_eval_func"]
        result = await func()
    except Exception:
        exc = traceback.format_exc()

    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr

    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = str(result)

    final_output = f"<b>Expression:</b>\n<code>{cmd}</code>\n\n<b>Result:</b>\n<code>{evaluation}</code>"
    if len(final_output) > 4096:
        # Send as document if too long
        with open("/tmp/eval_output.txt", "w") as f:
            f.write(evaluation)
        await message.reply_document("/tmp/eval_output.txt", caption="📄 Eval Output")
        await msg.delete()
    else:
        await msg.edit_text(final_output)

@Client.on_message(filters.command(["sh", "shell"], prefixes=COMMAND_PREFIXES) & filters.user(OWNER_ID))
async def sh_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("💻 <b>Usage:</b> <code>/sh [terminal command]</code>")

    cmd = message.text.split(maxsplit=1)[1]
    msg = await message.reply_text(f"💻 <i>Running:</i> <code>{cmd}</code>...")

    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = proc.stdout or proc.stderr or "Executed successfully with no output."
    except Exception as e:
        output = str(e)

    if len(output) > 4000:
        output = output[:4000] + "\n...[truncated]"

    await msg.edit_text(f"💻 <b>Output:</b>\n<code>{output}</code>")

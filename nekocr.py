import telegram # -> telegram library
from telegram import ChatAction,InlineKeyboardButton, InlineKeyboardMarkup # -> get everything on chat like keyboard type, language etc.
from telegram.ext.dispatcher import run_async # -> run with async 
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters,CallbackQueryHandler
import logging
import os
import json
from functools import wraps

##########################################################################################################
# cloudmersive ocr api
import cloudmersive_ocr_api_client
from cloudmersive_ocr_api_client.rest import ApiException

# api 
API_KEY = os.environ.get("CLOUDMERSIVE_API","")

def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context,  *args, **kwargs)

    return command_func
##########################################################################################################

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

###########################################################################################################

# BOT action 

@run_async     
@send_typing_action
def start(update,context):
    """Send a message when the command /start is issued."""
    global first
    first=update.message.chat.first_name
    update.message.reply_text('Hi! '+str(first)+' \n\nWelcome to Optical Character Recognizer (OCR) Bot. Nyaa\n\nJust send a clear image to me and i will recognize the text in the image and send it as a message!\n\nIf you have a questions about how work this bot /help\n\nCredit @h1z1survivor',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text='Repository', url='https://github.com/niyaxneko/NekoOCR')],
    ]))

@run_async
@send_typing_action
def convert_image(update,context):
    global filename
    filename="userimg.jpg"
    global file_id
    file_id = update.message.photo[-1].file_id
    newFile=context.bot.get_file(file_id)
    newFile.download(filename)

    # get image from user
    global chat_id
    chat_id=update.message.chat_id
    
    # Get inline keyboard from user
    keyboard = [[InlineKeyboardButton("English", callback_data='ENG'),InlineKeyboardButton("Hindi", callback_data='HIN'), InlineKeyboardButton("Russian", callback_data='RUS'),InlineKeyboardButton("Czech", callback_data='CES')],
                [InlineKeyboardButton("Chinese simplified", callback_data='ZHO'), InlineKeyboardButton("Chinese Traditional", callback_data='ZHO-HANT'),InlineKeyboardButton("Japanese", callback_data='JPA'),InlineKeyboardButton("Indonesian", callback_data='IND')] ,
                [InlineKeyboardButton("Arabic", callback_data='ARA'),InlineKeyboardButton("Afrikans", callback_data='AFR'), InlineKeyboardButton("German", callback_data='DEU'),InlineKeyboardButton("French", callback_data='FRA')],
                [InlineKeyboardButton("Italian", callback_data='ITA'), InlineKeyboardButton("Urdu", callback_data='URD'),InlineKeyboardButton("Malayalam", callback_data='MAL'),InlineKeyboardButton("Tamil", callback_data='TAM')],
                [InlineKeyboardButton("Hebrew", callback_data='HEB'), InlineKeyboardButton ("Bengali" , callback_data='BEN'), InlineKeyboardButton ("Spanish", callback_data='SPA'), InlineKeyboardButton ("Persian",callback_data='FAS')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('BAAMM! I got the Image please wait, I would be process it 😋\nPlease Select Language : ', reply_markup=reply_markup)
    return convert_image

@run_async
def button(update, context):
    global query
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="Selected Language is: {}".format(query.data))
    

    configuration = cloudmersive_ocr_api_client.Configuration()
    configuration.api_key['Apikey'] = API_KEY
    api_instance = cloudmersive_ocr_api_client.ImageOcrApi(cloudmersive_ocr_api_client.ApiClient(configuration))
    try:
        lang=query.data
        api_response = api_instance.image_ocr_post(filename,language=lang)
        confidence=api_response.mean_confidence_level
        result = api_response.text_result
        context.bot.send_message(chat_id=chat_id , text="Yeay, here the result 🥰\nI Confidence : "+str(confidence*100)+"% \nExtracted text:\n")
        context.bot.send_message(chat_id=chat_id , text='<pre>'+str(result)+'</pre>', parse_mode = 'HTML')
    except ApiException as e:
        context.bot.send_message(chat_id=chat_id , text="Exception when calling ImageOcrApi->image_ocr_photo_to_text: %s\n" % e)
        try:
            os.remove('userimg.jpg')
        except Exception:
            pass
    return button

def help(update, context):
    update.message.reply_text("QnA\n\nID\n\nQ : Apakah sesi pilih bahasa itu sebagai translate bahasa?\nA : Tidak, itu difungsikan untuk menentukan output misal : anda mengupload text gambar dengan huruf *Kanji, maka pilih *Japanese untuk output yang sesuai dengan pembahasaannya dan berlaku juga dengan yang lainnya\n\nENG\n\nQ: Did the session select the language as a language translation?\nA: No, it is used to determine the output, for example: you upload the image text with the letters of *Kanji, then select button *Japanese for output that matches the language and applies to other Languages")
    return help

def main(): 
    bot_token=os.environ.get("BOT_TOKEN", "")
    updater = Updater(bot_token,use_context=True)
    dp=updater.dispatcher
    dp.add_handler(CommandHandler('start',start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(MessageHandler(Filters.photo, convert_image))
    dp.add_handler(CallbackQueryHandler(button))
    updater.start_polling()
    updater.idle()
 
 ############################################################################################################
	
if __name__=="__main__":
	main()

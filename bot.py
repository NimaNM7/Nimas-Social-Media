import telebot
import pandas as pd

token = ""
robot_url = ""

print("bot started")

bot = telebot.TeleBot(token)

ADMIN = 441894051
SECOND_ADMIN = 1289225759

USERS_FILE_NAME = "USERS.csv"
POSTS_FILE_NAME = "POSTS.csv"
REPLIES_FILE_NAME = "REPLIES.csv"

CHANNEL_URL = ""
WELCOM_MESSAGE = f"""سلام عزیزم خوش اومدی به ربات خودت
قبل از هرکاری حواست باشه که تو کانال ما جوین بدی!
{CHANNEL_URL}

برای فرستادن پست برای همه اعضای ربات کافیه هر چی دلت خواست رو اینجا بنویسی و برای اینکه به پستای دوستات واکنش نشون بدی هم کافیه خیلی ساده رو پیامشون ریپلای بزنی تا نظرتو به شکل ناشناس ببینن و جوابتو بدن
امیدوارم لذت ببری"""

users_db = pd.read_csv(USERS_FILE_NAME)
posts_db = pd.read_csv(POSTS_FILE_NAME)
replies_db = pd.read_csv(REPLIES_FILE_NAME)

users_list = []
users_dict = {}
last_posts_dict = {}

def find_user_with_id(id: str) :
    if len(users_dict.keys()) == 0 :
        for index, row in users_db.iterrows() :
            users_dict[str(row["ID"])] = (index, str(row["USERNAME"]), int(row["STATUS"]))
    elif id not in users_dict.keys() :
        found = 0
        for index, row in users_db.iterrows() :
            if str(row["ID"]) == str(id) :
                found = 1
                users_dict[id] = (index, str(row["USERNAME"]), int(row["STATUS"]))
        if found == 0 :
            return None         
    return users_dict[id]

def find_user_with_username(username: str) :
    for index, row in users_db.iterrows() :
        if str(row["USERNAME"]) == username :
            return (index, row)
    return None

def find_post_with_id(id: str) :
    if len(last_posts_dict.keys()) == 0 :
        init_post_dict()
    elif id not in last_posts_dict.keys() :
        for index, row in posts_db.iterrows() :
            if str(row["ID"]) == id :
                return (index, row)
        return None
    return last_posts_dict[id]

def init_post_dict() :
    for index, row in posts_db.tail(100).iterrows() :
        last_posts_dict[str(row["ID"])] = (index, row)

def find_reply_with_id(id: str) :
    for index, row in replies_db.iterrows() :
        if str(row["ID"]) == id :
            return (index, row)
    return None

def find_all_users_ids() -> list :
    if len(users_list) == 0 :
        for index, row in users_db.iterrows() :
            if row["ID"] in users_list or row["STATUS"] == 2 :
                continue
            users_list.append(row["ID"])
    return users_list

def find_all_users() -> list :
    ids = []
    for index, row in users_db.iterrows() :
        ids.append(row["ID"])
    return ids

def get_type_and_id(message) :
    if message.text is not None :
        text = message.text
    else :
        text = message.caption

    if text.startswith("#post") :
        message_type = 2
    else :
        message_type = 1
    id = text.split(" ")[1]
    return (message_type, id)

def make_post_caption_format(id, text) -> str :
    if text is not None and text != "nan":
        return f"#post {id} \n\n{text} \n\n{robot_url}"
    return f"#post {id} \n\n{robot_url}"

def make_reply_format(id, text) -> str :
    return f"#reply {id} \n\n{text}"

def save_reply(id, sender_id, receiver_id, context, post_id) :
    new = {
        "ID" : id,
        "SENDER_ID" : sender_id,
        "RECEIVER_ID" : receiver_id,
        "CONTEXT" : context,
        "POST_ID" : post_id
    }

    replies_db.loc[len(replies_db)] = new
    replies_db.to_csv(REPLIES_FILE_NAME, index=False)

def save_post(id, sender_id, text, media_id, content_type) :
    new = {
        "ID" : id,
        "SENDER_ID" : sender_id,
        "TEXT" : text,
        "CONTENT_TYPE" : content_type
    }
    if media_id is not None :
        new["MEDIA_ID"] = media_id

    posts_db.loc[len(posts_db)] = new
    if len(last_posts_dict.keys()) == 0:
        init_post_dict()
    last_posts_dict[id] = (len(posts_db) - 1, new)
    posts_db.to_csv(POSTS_FILE_NAME, index= False)


def reply_handler(message) :
    original_message = message.reply_to_message
    original = get_type_and_id(original_message)
    if original[0] == 1 :
        receiver = find_reply_with_id(original[1])
        post_id = receiver[1]["POST_ID"]
    else :
        receiver = find_post_with_id(original[1])
        print(f"post id {receiver}")
        post_id = receiver[1]["ID"]

    original_message_id = original[1]

    receiver_id = receiver[1]["SENDER_ID"]
    final_message = make_reply_format(message.id, message.text)

    if message.from_user.id == receiver_id :
        return

    save_reply(message.id, message.from_user.id, receiver_id, message.text, post_id)
    bot.send_message(receiver_id, final_message, reply_to_message_id= original_message_id)
    bot.send_message(SECOND_ADMIN, final_message) # for test

def text_post_handler(message) :
    final_message = make_post_caption_format(message.id, message.text)
    save_post(message.id, message.from_user.id, message.text, None, 0)
    # bot.send_message(ADMIN, final_message)
    all_users = find_all_users_ids()
    for user in all_users :
        try :
            bot.send_message(user, final_message)
        except Exception as e :
            print(f"problem with sending to {user} {e}")
            if "block" in str(e) :
                blocking_user = find_user_with_id(user)
                users_db.at[blocking_user[0], "STATUS"] = 2
                users_db.to_csv(USERS_FILE_NAME, index= False)
    bot.reply_to(message, "پست با موفقیت فرستاده شد.")

def media_is_comment(message) :
    if message.reply_to_message :
        bot.reply_to(message, "کامنت و مکالمه های ناشناس قابلیت اضافه کردن مدیا را ندارند.")
        return True
    return False

def media_handler(message, media_type) :
    if media_is_comment(message) :
        return

    caption = message.caption
    final_caption = make_post_caption_format(message.id, caption)

    if media_type == 'photo' :
        file_id = message.photo[-1].file_id
        bot.send_photo(ADMIN, photo= file_id, caption= final_caption)
        type_id = 1
    elif media_type == 'video' :
        file_id = message.video.file_id
        bot.send_video(ADMIN, video= file_id, caption= final_caption)
        type_id = 2
    elif media_type == 'audio' :
        file_id = message.audio.file_id
        bot.send_audio(ADMIN, audio= file_id, caption= final_caption)
        type_id = 3
    elif media_type == 'voice' :
        file_id = message.voice.file_id
        bot.send_voice(ADMIN, voice= file_id, caption= final_caption)
        type_id = 4

    save_post(message.id, message.from_user.id, message.caption, file_id, type_id)
    bot.send_photo(message, photo= file_id, caption= final_caption)
    bot.reply_to(message, "پست شما با موفقیت ارسال شد")

def send_post_with_id(post_id, users:list) :
    post = find_post_with_id(post_id)
    content_type = int(post[1]["CONTENT_TYPE"])
    caption = make_post_caption_format(post_id, post[1]["TEXT"])
    file_id = post[1]["MEDIA_ID"]

    if content_type == 0 :
        for user_id in users :
            try:
                bot.send_message(user_id, caption)
            except :
                print(f"problem with sending to {user_id}")
    elif content_type == 1 :
        for user_id in users :
            try :
                bot.send_photo(user_id, photo= file_id, caption= caption)
            except :
                print(f"problem with sending to {user_id}")
    elif content_type == 2 :
        for user_id in users :
            try :
                bot.send_video(user_id, video= file_id, caption= caption)
            except :
                print(f"problem with sending to {user_id}")
    elif content_type == 3 :
        for user_id in users :
            try :
                bot.send_audio(user_id, audio= file_id, caption= caption)
            except :
                print(f"problem with sending to {user_id}")
    elif content_type == 4 :
        for user_id in users :
            try :
                bot.send_voice(user_id, voice= file_id, caption= caption)
            except :
                print(f"problem with sending to {user_id}")


@bot.message_handler(commands=['start'])
def start(message) :
    bot.reply_to(message, WELCOM_MESSAGE)
    user_id = message.from_user.id
    if find_user_with_id(user_id) is not None :
        return
    username = message.from_user.username
    new = {
        "ID" : user_id,
        "USERNAME" : username,
        "NAME" : message.from_user.first_name
    }
    bot.send_message(ADMIN, f"we have new user : {new}")
    users_db.loc[len(users_db)] = new
    users_list.append(user_id)
    users_dict[user_id] = (len(users_db) - 1, username, 0)
    users_db.to_csv(USERS_FILE_NAME, index= False)

@bot.message_handler(commands=['sub'])
def submit(message) :
    if message.from_user.id != ADMIN and message.from_user.id != SECOND_ADMIN :
        bot.reply_to(message, "دسترسی به این بخش برای شما مجاز نیست")
        return
    
    if not message.reply_to_message :
        bot.reply_to(message, "رو یه پیام ریپلای کن نیما جان")
        return
    
    original_message = message.reply_to_message
    original = get_type_and_id(original_message)
    post_id = original[1]
    post = find_post_with_id(post_id)
    all_users = find_all_users_ids()
    send_post_with_id(post_id, all_users)

    bot.reply_to(message, "پست مورد نظر با موفقیت سابمیت شد")

@bot.message_handler(commands=['backup'])

def backup(message) :
    if message.from_user.id != ADMIN :
        bot.reply_to(message, "دسترسی به این بخش برای شما مجاز نیست")
        return
    
    try :
        with open("USERS.csv", "r") as users:
            bot.send_document(ADMIN, users)
        with open("POSTS.csv","r") as posts :
            bot.send_document(ADMIN, posts)
        with open("REPLIES.csv", "r") as replies :
            bot.send_document(ADMIN, replies)
    except Exception as e :
        bot.reply_to(message, e)
        
@bot.message_handler(commands = ['announce'])
def announce(message) :
    if message.from_user.id != ADMIN and message.from_user.id != SECOND_ADMIN :
        bot.reply_to(message, "دسترسی به این بخش برای شما مجاز نیست")
        return
    
    text = str(message.text)[10:]
    users = find_all_users_ids()
    for user in users :
        bot.send_message(user, f"#admin\n{text}")

@bot.message_handler(content_types=['text'])
def main_handler(message) :
    if message.reply_to_message :
        reply_handler(message)
    else :
        text_post_handler(message)

@bot.message_handler(content_types=['photo'])
def photo_handler(message) :
    media_handler(message, 'photo')

@bot.message_handler(content_types=['video'])
def video_handler(message) :
    media_handler(message, 'video')

@bot.message_handler(content_types=['audio'])
def audio_handler(message) :
    media_handler(message, 'audio')

@bot.message_handler(content_types=['voice'])
def voice_handler(message) :
    media_handler(message, 'voice')


bot.infinity_polling()
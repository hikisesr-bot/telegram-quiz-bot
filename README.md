# **Full Guide: From Web App Idea to 24/7 Telegram Bot**

This document summarizes the complete process we went through to transform your HTML web app into a fully functional, 24/7 Telegram bot hosted for free on Choreo.

### **Stage 1: The Initial Idea and First Bot (Polling Method)**

Our journey started with a simple goal: to turn your "Dudai's Academy" HTML quiz generator into a Telegram bot.

1. **Code Translation:** We analyzed the JavaScript code in your Quiz.html file and translated all of its logic into a Python script named bot.py.  
2. **Core Technology:** This first version used a method called **long polling**. The key line of code was bot.infinity\_polling(). This method works by constantly asking Telegram's servers, "Is there a new message for me?" over and over again. While simple, we later discovered this method is not ideal for "serverless" platforms like Choreo.

### **Stage 2: Preparing for Deployment (GitHub)**

To run a bot 24/7, you need to host its code on a server. We used Choreo for this, but first, we had to store the code where Choreo could find it.

1. **Create a GitHub Repository:** We created a public repository on GitHub (e.g., telegram-quiz-bot). This acts as the central storage for your code.  
2. **Create Project Files:** We created three essential files:  
   * bot.py: The main Python script containing all the bot's logic.  
   * requirements.txt: A list of the Python libraries the bot needs to run (like pyTelegramBotAPI and python-docx).  
   * Procfile: A single-line file that tells the hosting service (Choreo) exactly how to start your bot (e.g., worker: python bot.py).

### **Stage 3: Troubleshooting and The "Sleeping Bot" Problem**

This was our biggest challenge. After deploying the first version of the bot to Choreo, it would run for a few minutes and then stop responding.

We diagnosed several issues:

* **Build Failures:** Our first builds failed because of an error in the requirements.txt file. We fixed this by removing extra text from the file on GitHub and starting a new build.  
* **"Crash Loop Back Off":** The bot was crashing immediately upon starting. We checked the **Runtime Logs** in Choreo to find the error.  
* **Incorrect API Token:** The logs showed a 401 Unauthorized error, which meant the API token was wrong. We fixed this by getting a new token from the BotFather and updating the secret in Choreo's **Configs & Secrets** section.  
* **The Real Problem \- "Scale to Zero":** The main issue was that Choreo's free plan is designed to save resources by putting idle applications to sleep. Our bot, which was constantly "polling," was seen as idle and was being shut down. Even setting the "No Autoscaling" option did not permanently solve this.

### **Stage 4: The Final, Permanent Solution (Webhook Method)**

To solve the "sleeping bot" problem for good, we upgraded the bot to use a more professional and reliable method called **webhooks**.

1. **How Webhooks Work:** Instead of your bot constantly asking for messages, you give Telegram a unique URL (your bot's public address). When a user sends a message, Telegram sends it directly to that URL. This is much more efficient and is fully supported by platforms like Choreo.  
2. **Code Upgrade:**  
   * We updated bot.py to include a simple web server using a library called **Flask**.  
   * We removed the bot.infinity\_polling() line.  
   * We added code to automatically set the webhook by visiting the bot's public URL one time.  
3. **File Updates:**  
   * We updated requirements.txt to include Flask and gunicorn.  
   * We updated the Procfile to tell Choreo how to run the new web server: web: gunicorn bot:app.  
4. **Final Choreo Configuration:**  
   * We added a new secret to **Configs & Secrets** for the WEBHOOK\_URL.  
   * We went to the **Deploy \-\> Endpoints** page and changed the **Network Visibility** of our bot's URL from "Private" to **"Public"**. This was the final lock we had to open so Telegram could reach our bot.  
   * We activated the connection by visiting the public URL in a browser, which displayed the Webhook set\! message.

After completing these final steps, the bot became fully operational, stable, and will now run 24/7 without ever falling asleep. Congratulations on your hard work and persistence\!
# TRADER ANIKE AI — সোর্স কোড

এটি একটি শিক্ষামূলক চার্ট-স্ক্রিনশট বিশ্লেষণ প্রোটোটাইপ। এটি Quotex-এর সঙ্গে সরাসরি সংযুক্ত নয়, লাইভ মার্কেট ডেটা পায় না এবং নিজে ট্রেড করে না।

## কী আছে
- স্ক্রিনশট আপলোড (PNG/JPG/WEBP)
- OpenAI vision model দিয়ে চার্টের দৃশ্যমান তথ্য বিশ্লেষণ
- UP / DOWN / WAIT এবং আনুমানিক শতাংশ
- ছবিতে দাম পড়া গেলে সম্ভাব্য এন্ট্রি/রাউন্ড-নাম্বার লেভেল
- বাংলা ব্রাউজার ভয়েস অ্যালার্ট

## আগে যা লাগবে
- Python 3.10 বা তার নতুন সংস্করণ
- OpenAI API account এবং API key; API ব্যবহারে খরচ হতে পারে
- সার্ভার চালানোর জন্য কম্পিউটার/হোস্টিং। শুধু ZIP ডাউনলোড করলেই Android-এ ব্যাকএন্ড চলবে না।

## চালানোর নিয়ম (Windows / Mac / Linux)
1. ZIP extract করুন এবং ফোল্ডারে ঢুকুন।
2. Terminal/Command Prompt খুলে চালান:

   ```bash
   python -m venv .venv
   ```

3. Environment activate করুন:

   Windows:
   ```bash
   .venv\Scripts\activate
   ```

   Mac/Linux:
   ```bash
   source .venv/bin/activate
   ```

4. Dependencies ইনস্টল করুন:

   ```bash
   pip install -r requirements.txt
   ```

5. `.env.example` ফাইলের কপি করে `.env` নাম দিন। `.env` ফাইলে নিজের API key দিন:

   ```text
   OPENAI_API_KEY=your_real_api_key_here
   OPENAI_MODEL=gpt-4.1-mini
   ```

   API key কখনো HTML/JavaScript-এ লিখবেন না, কাউকে পাঠাবেন না, GitHub-এ আপলোড করবেন না।

6. সার্ভার চালান:

   ```bash
   uvicorn app:app --host 127.0.0.1 --port 8000
   ```

7. একই কম্পিউটারের ব্রাউজারে `http://127.0.0.1:8000` খুলুন।

## Android ফোনে কীভাবে ব্যবহার করবেন
Backend-টি একটি নিরাপদ HTTPS hosting service-এ deploy করতে হবে, তারপর সাইটটি Chrome-এ খুলতে হবে। শুধু ফোনে `index.html` খোললে AI API কল হবে না। ফোন ও কম্পিউটার একই Wi-Fi-তে থাকলে লোকাল সার্ভারের private IP দিয়ে টেস্ট করা যায়, তবে `--host 0.0.0.0` ব্যবহার করলে নেটওয়ার্কের অন্য ডিভাইসও সার্ভার দেখতে পারে; বিশ্বস্ত নেটওয়ার্ক ছাড়া এটি করবেন না।

## গুরুত্বপূর্ণ সীমাবদ্ধতা
- UP/DOWN শতাংশ মডেলের ছবি-ভিত্তিক আনুমানিক মতামত; calibrated probability বা প্রমাণিত win rate নয়।
- ৫-সেকেন্ডের ক্যান্ডেল খুব দ্রুত বদলায়; স্ক্রিনশট বিশ্লেষণ ততক্ষণে পুরোনো হয়ে যেতে পারে।
- স্ক্রিনশটে price scale পরিষ্কার না হলে entry/round level ফাঁকা থাকবে।
- এই প্রোটোটাইপ কোনো স্বয়ংক্রিয় ট্রেড বা লাভের নিশ্চয়তা দেয় না। আগে demo-তে ফলাফল নথিভুক্ত করে যাচাই করুন।

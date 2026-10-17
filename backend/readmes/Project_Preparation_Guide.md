# 🎓 Xephy-AI: Project Defense Cheat Sheet

Yeh document aapki Final Project Presentation / Viva ki tayari ke liye banaya gaya hai. Is mein un tamam files aur technical decisions ki wazahat hai jo aapse poochi ja sakti hain.

> **Architecture status:** Yeh guide kuch purane implementation decisions ko describe karti hai. Current project scope, database setup, aur safety boundaries ke liye [current architecture](../../ARCHITECTURE.md) aur root README ko follow karein.

---

## 1. 📂 Special Files & Unka Maqsad

Project mein kuch aisi files hain jo aam coding se thori alag hain:

| File Type / Name | Yeh kya hai aur kyun hai? |
| :--- | :--- |
| **`__init__.py`** | Yeh file har folder mein isliye rakhi jati hai taake Python us folder ko aik **"Package"** (Library) samjhe. Iske baghair hum files ko ek doosre mein `import` nahi kar sakte (jaise `from src.trading_system import main`). Aksar yeh file khali (empty) hoti hai. |
| **`.pkl` (Pickle)** | Python object serialization format. No verified model artifact is currently shipped; a generated model is not evidence of accuracy and must be evaluated before use. |
| **`.sh` (Shell Script)** | `train_ml.sh`. Yeh Linux/Mac ka batch script hota hai. Iska maqsad lambi commands (`python -m src...`) ko aik choti command (`bash train_ml.sh`) mein automate karna hai. |
| **Database** | SQLAlchemy ORM aur Alembic migrations use hote hain. Current local development PostgreSQL par configured hai; SQLite fresh/local fallback hai. Trade history transfer se pehle backup zaroor karein. |
| **`.env` (Environment)**| Is file mein aisi settings aur passwords (credentials) save hote hain jinhe hum public code (GitHub) par show nahi karna chahte. |

---

## 2. 🏗️ Backend Folder Structure (Architecture)

Aapke `backend/src/trading_system/` ka architecture "Modular" hai (yani har kaam ka alag department hai). Is se code ko manage karna asaan hota hai:

- **`/market`**: Isme synthetic development data (`MockMT5`) aur read-only MT5 data (`RealMT5`) adapters hain. Neither adapter submits broker trades.
- **`/indicators`**: Yahan Technical Indicators (RSI, MACD, EMA) calculate hote hain.
- **`/smc`**: Yeh Smart Money Concepts (BOS, Order Blocks, Liquidity Grabs) ka department hai.
- **`/core`**: Yahan `signal_aggregator.py` mojood hai. Yeh sab departments se results le kar final faisla karta hai (BUY ya SELL).
- **`/ai`**: Yahan Machine Learning (XGBoost) model ki training aur predictions hoti hain.
- **`/risk`**: Yeh department tay karta hai ke Lot Size (Position Size) kya hoga aur Stop Loss / Take Profit kahan lagana hai.
- **`/execution`**: Yeh department final order ko broker (MT5) tak pohnchata hai.

---

## 3. 🧠 Key Coding Decisions (Important Q&A)

Agar panel ya teacher aapse yeh sawalat poochein, toh aap yeh jawab de sakte hain:

### Q1: Aapne `MockMT5` kyun banaya jabke trade MT5 par karni thi?
**Answer:** MetaTrader 5 (MT5) ki Python library sirf **Windows** par support hoti hai. Kyun ke humari development Linux par ho rahi thi (ya ML models Colab par train hote hain), isliye humne `MockMT5` banaya jo bilkul real MT5 ki tarah behave karta hai aur fake data generate karta hai. Jab hum Windows par shift hote hain toh hum `.env` mein `MOCK_MT5=false` kar ke directly **RealMT5** par switch kar lete hain bina baki code change kiye.

### Q2: XGBoost ko hi kyun choose kiya Deep Learning (Neural Networks) ke bajaye?
**Answer:** Trading ka data "Tabular Data" (OHLCV) hota hai. Tabular data par XGBoost jese Tree-based models Neural Networks se zyada fast aur accurate hote hain. Neural networks ko train karne ke liye bohat zyada data (millions of rows) aur GPUs chahiye hote hain, jabke XGBoost chote data (5000 candles) par bhi overfitting ke baghair achi accuracy de deta hai.

### Q3: `signal_aggregator` ka kya maqsad hai? AI direct trade kyun nahi lagata?
**Answer:** Hum "Black-box" AI nahi banana chahte the. Hamara system **Hybrid Approach** use karta hai:
1. Pehle Technical Indicators apna score dete hain.
2. Phir SMC (Price Action) apna trend batata hai.
3. Agar in dono mein "Consensus" (mutafeqa faisla) ho, tabhi AI XGBoost se confirm karwa kar trade lagata hai. Is se accuracy bohat barh jati hai.

### Q4: Dashboard ke liye React aur Backend ke liye Flask kyun? (Decoupled Architecture)
**Answer:** Hum chahte the ke humara A.I engine bilkul alag rahay aur UI alag. Agar kal ko humein Mobile App (React Native) banani paray, toh humein Python code change nahi karna parega, hamari Flask API wese hi kaam karti rahegi.

---

> [!TIP]
> **Best Practice for Defense:** Apne system ko **"Hybrid AI Trading System"** bolain, jo SMC (Smart Money Concepts), Technical Analysis, aur Machine Learning ka majmooa (combination) hai. Yeh aapke project ko bohat advance banata hai!

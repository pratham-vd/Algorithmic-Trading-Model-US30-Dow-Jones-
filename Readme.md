## Algorithmic Trading Model – US30 (Dow Jones)

A Python-based algorithmic trading system designed to capture volatility during a fixed market event (8 PM IST).  
The strategy automates trade execution using a breakout approach and is built with a strong focus on risk management, timing precision, and reliability.


## Overview

This project implements a rule-based intraday trading strategy for US30 (Dow Jones Index).  
The system captures price just before a high-volatility event and places pending orders on both sides to catch breakouts.

The goal is to eliminate manual intervention and handle fast market conditions with precise, time-based execution.


## Strategy Logic

- Capture price **15 seconds before 8:00 PM IST**
- Place:
  - Buy stop above current price  
  - Sell stop below current price  
- Fixed **risk per trade (1%)**
- Stop Loss placed at opposite entry level  
- Take Profit set at predefined distance  
- Once one order triggers → the other is automatically cancelled  


## Key Features

- Fully automated trade execution logic  
- Time-based event handling for high-volatility scenarios  
- Configurable parameters via a separate configuration file  
- End-to-end trade lifecycle management:
  - Entry → Monitoring → Exit → Logging  
- Trade results logged in CSV format for analysis  


## Project Structure

├── config.py # Strategy parameters (risk, SL/TP, entry distance)
├── strategy.py # Core trading logic
├── engine.py # Execution & trade management
├── data_loader.py # Market data handling
├── report.py # Performance & trade logging
├── api.py # Backend integration (FastAPI)


## Tech Stack

- Python  
- Pandas  
- FastAPI  
- NumPy  


## Use Case

This system is designed to:
- Handle **high-speed market conditions** where manual trading is difficult  
- Provide a **structured and repeatable trading approach**  
- Serve as a base for further improvements like backtesting and optimization  


##  Future Improvements

- Integration with live trading APIs  
- Advanced performance analytics  
- Strategy optimization using historical data  
- Potential extension to ML-based parameter tuning  


## Note

This project is built for educational and research purposes.  
Trading involves risk, and this system should be tested thoroughly before live deployment.



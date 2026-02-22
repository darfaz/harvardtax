# HarvardTax

Partnership/LLC tax return generator (IRS Form 1065 + Schedule K-1).

## Overview

HarvardTax connects to QuickBooks Online, pulls financial data for a partnership or LLC, maps it to IRS Form 1065 line items, and generates filled 1065 and K-1 PDFs.

## Stack

- **Backend:** Python / FastAPI
- **Frontend:** Next.js
- **Database:** Supabase
- **AI:** Claude (Anthropic) for intelligent field mapping
- **Integration:** QuickBooks Online API

## Getting Started

```bash
# Backend
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

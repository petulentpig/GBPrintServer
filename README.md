# GBPrintServer

Shopify webhook listener that automatically prints a QR code for each new order and sends a Slack notification.

## How it works

1. Shopify sends an `orders/create` webhook to this server
2. Server generates a QR code linking to the order admin page
3. QR code is printed via PrintNode (cloud printing)
4. A Slack notification is sent with order details

## Setup

### Environment Variables

| Variable | Description |
|---|---|
| `SHOPIFY_WEBHOOK_SECRET` | Shopify webhook HMAC secret |
| `SHOPIFY_STORE_URL` | Your store domain (e.g. `mystore.myshopify.com`) |
| `PRINTNODE_API_KEY` | PrintNode API key |
| `PRINTNODE_PRINTER_ID` | PrintNode printer ID |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |

### Local Development

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in your values
python app.py
```

### Deploy to Railway

1. Connect this repo to Railway
2. Set the environment variables in Railway dashboard
3. Railway will auto-detect the Procfile

### Shopify Webhook

In Shopify Admin > Settings > Notifications > Webhooks, create a webhook:
- Event: **Order creation**
- URL: `https://your-railway-url.up.railway.app/webhook/orders`
- Format: JSON

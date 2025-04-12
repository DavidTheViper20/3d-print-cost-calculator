// Required dependencies
const express = require('express');
const { shopifyApi, ApiVersion } = require('@shopify/shopify-api');
const { restResources } = require('@shopify/shopify-api/rest/admin/2023-04');
const { nodeAdapter } = require('@shopify/shopify-api/adapters/node');

// Create Express app
const app = express();

// Initialize Shopify API client
const shopify = shopifyApi({
  apiKey: 'cbdd4422bfee8475893c474b9be62c6b',
  apiSecretKey: '18fac7f63bb75dc14c0b245b50f51f52',
  scopes: ['write_products', 'read_orders'],
  hostName: 'threed-print-cost-calculator.onrender.com',
  apiVersion: ApiVersion.April23, // or '2023-04'
  isEmbeddedApp: true,
  restResources,
  adapter: nodeAdapter,
});

// Route to test the setup
app.get('/', (req, res) => {
  res.send('✅ Shopify v11 API initialized with Node adapter!');
});

// Start the server
const PORT = 3000;
app.listen(PORT, () => {
  console.log(`🚀 Server running at http://localhost:${PORT}`);
});
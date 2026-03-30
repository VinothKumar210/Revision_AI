
const { PrismaClient } = require('@prisma/client');
require('dotenv').config({ path: '.env.local' });
const prisma = new PrismaClient({
  datasources: { db: { url: process.env.DATABASE_URL } }
});
async function main() {
  const url = process.env.DATABASE_URL || '';
  console.log('Testing connection to: ' + url.replace(/:([^:@]{3,})@/, ':***@'));
  const count = await prisma.user.count();
  console.log('? Database is ONLINE and CONNECTED! Current users in DB: ' + count);
  process.exit(0);
}
main().catch(e => { console.error('? Connection failed:', e); process.exit(1); });


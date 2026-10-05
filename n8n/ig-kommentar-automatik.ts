import { workflow, node, trigger, ifElse, expr } from '@n8n/workflow-sdk';

const verifyIn = trigger({
  type: 'n8n-nodes-base.webhook', version: 2.2,
  config: { name: 'Meta-Pruefung', parameters: { httpMethod: 'GET', path: 'ig-events', authentication: 'none', responseMode: 'responseNode' } }
});
const tokenOk = ifElse({ version: 2.3, config: { name: 'Pruefwort stimmt?', parameters: { conditions: {
  options: { caseSensitive: true, typeValidation: 'loose' },
  conditions: [ { id: 'v1', leftValue: expr('{{ $json.query["hub.verify_token"] }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'walkzy-verify-2026' } ], combinator: 'and' } } } });
const answerChallenge = node({ type: 'n8n-nodes-base.respondToWebhook', version: 1.5, config: { name: 'Challenge zurueck', parameters: { respondWith: 'text', responseBody: expr('{{ $json.query["hub.challenge"] }}') } } });
const answerNo = node({ type: 'n8n-nodes-base.respondToWebhook', version: 1.5, config: { name: 'Abgelehnt', parameters: { respondWith: 'text', responseBody: 'nein', options: { responseCode: 403 } } } });

const eventsIn = trigger({
  type: 'n8n-nodes-base.webhook', version: 2.2,
  config: { name: 'Meta-Ereignis', parameters: { httpMethod: 'POST', path: 'ig-events', authentication: 'none', responseMode: 'onReceived' } }
});
const getConfig = node({ type: 'n8n-nodes-base.dataTable', version: 1.1, config: { name: 'Zugangsdaten laden', parameters: {
  resource: 'row', operation: 'get', dataTableId: { __rl: true, mode: 'id', value: 'OxfiiJCPtzGmKEzv' }, returnAll: true } } });
const prepare = node({ type: 'n8n-nodes-base.code', version: 2, config: { name: 'Vorbereiten', parameters: { mode: 'runOnceForAllItems', language: 'javaScript',
  jsCode: `const cfg = {};
for (const r of $input.all()) { cfg[r.json.key] = r.json.value; }
const body = $('Meta-Ereignis').first().json.body || {};
const dm = 'Hallo, danke für deinen Kommentar! Walkzy richtet kleinen Betrieben eine automatische Antwort für Anfragen ein, auch nachts und am Wochenende. Was für einen Betrieb hast du, und wonach fragen dich Kunden am häufigsten? Wir melden uns dann persönlich bei dir.';
const out = [];
for (const e of (body.entry || [])) {
  for (const c of (e.changes || [])) {
    if (c.field !== 'comments') continue;
    const v = c.value || {};
    if (!/automatik/i.test(v.text || '')) continue;
    if (v.from && v.from.id === cfg.ig_user_id) continue;
    if (v.parent_id) continue;
    out.push({ json: { comment_id: v.id, text: v.text, username: (v.from || {}).username || '', ig_user_id: cfg.ig_user_id, ig_access_token: cfg.ig_access_token, dm } });
  }
}
return out;` } } });
const sendDm = node({ type: 'n8n-nodes-base.httpRequest', version: 4.4, config: { name: 'Private Antwort senden', parameters: {
  method: 'POST', url: expr('https://graph.instagram.com/v23.0/{{ $json.ig_user_id }}/messages'),
  sendQuery: true, specifyQuery: 'keypair', queryParameters: { parameters: [ { name: 'access_token', value: expr('{{ $json.ig_access_token }}') } ] },
  sendBody: true, contentType: 'json', specifyBody: 'json',
  jsonBody: expr('{{ JSON.stringify({ recipient: { comment_id: $json.comment_id }, message: { text: $json.dm } }) }}') } } });
const mail = node({ type: 'n8n-nodes-base.gmail', version: 2.2, config: { name: 'Mail: neuer Lead', parameters: { resource: 'message', operation: 'send', sendTo: 'lavan460@gmail.com', emailType: 'text',
  subject: expr('Walkzy Lead: @{{ $("Vorbereiten").item.json.username }} hat AUTOMATIK kommentiert'),
  message: expr('Kommentar: {{ $("Vorbereiten").item.json.text }}\n\nDie automatische DM wurde gesendet. Antwort von Instagram: {{ JSON.stringify($json) }}\n\nWenn die Person antwortet, ist sie in deinen Instagram-Nachrichten.') },
  credentials: { gmailOAuth2: { id: 'AYc7PGKtHRRXAHtf', name: 'Gmail account' } } } });

export default workflow('ig-comment-auto', 'Instagram: Kommentar-Automatik')
  .add(verifyIn).to(tokenOk.onTrue(answerChallenge).onFalse(answerNo))
  .add(eventsIn).to(getConfig).to(prepare).to(sendDm).to(mail);

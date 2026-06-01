import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    loopers_latency: {
      executor: 'constant-vus',
      vus: 500,
      duration: '60s',
      env: { PROXY_URL: 'http://localhost:4000/openai/v1/chat/completions', API_KEY: 'lp-looperstestkey12345678901234567890123456789' },
    },
    litellm_latency: {
      executor: 'constant-vus',
      vus: 500,
      duration: '60s',
      env: { PROXY_URL: 'http://localhost:4001/v1/chat/completions', API_KEY: 'sk-litellm-test' },
    }
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
  },
};

if (__ENV.PROXY === 'loopers') {
    delete options.scenarios.litellm_latency;
} else if (__ENV.PROXY === 'litellm') {
    delete options.scenarios.loopers_latency;
} else {
    throw new Error('Please set PROXY=loopers or PROXY=litellm');
}

export default function () {
  const url = __ENV.PROXY_URL;
  const payload = JSON.stringify({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: 'hello' }],
    max_tokens: 50
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${__ENV.API_KEY}`,
    },
  };

  const res = http.post(url, payload, params);

  check(res, {
    'is status 200': (r) => r.status === 200,
  });
}

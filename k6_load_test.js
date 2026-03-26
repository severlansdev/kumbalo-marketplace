import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const motoListLatency = new Trend('moto_list_latency');

// Test configuration
export const options = {
    stages: [
        { duration: '1m', target: 20 },   // Ramp up to 20 users
        { duration: '3m', target: 50 },   // Hold at 50 users
        { duration: '2m', target: 100 },  // Stress test: 100 users
        { duration: '1m', target: 0 },    // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<800', 'p(99)<2000'],  // SLO: p95 < 800ms
        http_req_failed: ['rate<0.01'],                   // SLO: <1% error rate
        errors: ['rate<0.05'],
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
    group('Homepage API', () => {
        const res = http.get(`${BASE_URL}/`);
        check(res, {
            'status is 200': (r) => r.status === 200,
            'response has message': (r) => r.json().message !== undefined,
        });
        errorRate.add(res.status !== 200);
    });

    group('Health Check', () => {
        const res = http.get(`${BASE_URL}/health`);
        check(res, {
            'health is 200': (r) => r.status === 200,
            'status is healthy': (r) => r.json().status === 'healthy',
        });
    });

    group('List Motos', () => {
        const start = Date.now();
        const res = http.get(`${BASE_URL}/motos/?skip=0&limit=20`);
        motoListLatency.add(Date.now() - start);
        check(res, {
            'motos status 200': (r) => r.status === 200,
            'motos is array': (r) => Array.isArray(r.json()),
        });
        errorRate.add(res.status !== 200);
    });

    group('Search Motos', () => {
        const res = http.get(`${BASE_URL}/motos/?marca=yamaha&limit=10`);
        check(res, {
            'search status 200': (r) => r.status === 200,
        });
    });

    sleep(1); // Think time between iterations
}

export function handleSummary(data) {
    return {
        'stdout': textSummary(data, { indent: ' ', enableColors: true }),
        'load_test_results.json': JSON.stringify(data, null, 2),
    };
}

function textSummary(data) {
    return `
=== KUMBALO Load Test Results ===
Total Requests: ${data.metrics.http_reqs.values.count}
Avg Duration: ${Math.round(data.metrics.http_req_duration.values.avg)}ms
P95 Duration: ${Math.round(data.metrics.http_req_duration.values['p(95)'])}ms
P99 Duration: ${Math.round(data.metrics.http_req_duration.values['p(99)'])}ms
Error Rate: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%
`;
}

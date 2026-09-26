import http from "k6/http";
import { check } from "k6";
import { Counter } from "k6/metrics";

// ============================================================
// CONFIG
// ============================================================

const BASE_URL = "http://127.0.0.1:8000";
const DROP_ID = 9;

// Load JWT tokens
const tokens = JSON.parse(open("./load_test_tokens.json"));

// ============================================================
// METRICS
// ============================================================

const status201 = new Counter("status_201");
const status400 = new Counter("status_400");
const status401 = new Counter("status_401");
const status409 = new Counter("status_409");
const status500 = new Counter("status_500");
const otherStatus = new Counter("other_status");

const requestErrors = new Counter("request_errors");
const reservationSuccess = new Counter("reservation_success");
const reservationUnavailable = new Counter("reservation_unavailable");

// ============================================================
// K6 OPTIONS
// ============================================================

export const options = {
    scenarios: {
        reservation_load: {
            executor: "shared-iterations",
            vus: 100,
            iterations: 100,
            maxDuration: "2m",
        },
    },
};

// ============================================================
// RESERVATION TEST
// ============================================================

export default function () {

    // --------------------------------------------------------
    // Select token for current VU
    // --------------------------------------------------------

    const userIndex = (__VU - 1) % tokens.length;
    const tokenData = tokens[userIndex];

    if (!tokenData || !tokenData.token) {
        requestErrors.add(1);

        console.log(
            `TOKEN_ERROR | VU=${__VU} | userIndex=${userIndex}`
        );

        return;
    }

    // --------------------------------------------------------
    // API URL
    // --------------------------------------------------------

    const url =
        `${BASE_URL}/api/drops/drops/${DROP_ID}/reserve/`;

    // --------------------------------------------------------
    // Send reservation request
    // --------------------------------------------------------

    const response = http.post(
        url,
        JSON.stringify({}),
        {
            headers: {
                Authorization: `Bearer ${tokenData.token}`,
                "Content-Type": "application/json",
                Accept: "application/json",
            },
        }
    );

    // --------------------------------------------------------
    // Request / Network Error
    // --------------------------------------------------------

    if (response.error) {

        requestErrors.add(1);

        console.log(
            `REQUEST_ERROR | VU=${__VU} | ` +
            `error=${response.error} | ` +
            `error_code=${response.error_code}`
        );

        return;
    }

    // --------------------------------------------------------
    // Status Handling
    // --------------------------------------------------------

    if (response.status === 201) {

        status201.add(1);
        reservationSuccess.add(1);

        console.log(
            `SUCCESS | VU=${__VU} | ` +
            `status=201 | ` +
            `body=${response.body}`
        );

    } else if (response.status === 409) {

        status409.add(1);
        reservationUnavailable.add(1);

        console.log(
            `UNAVAILABLE | VU=${__VU} | ` +
            `status=409 | ` +
            `body=${response.body}`
        );

    } else if (response.status === 400) {

        status400.add(1);

        console.log(
            `BAD_REQUEST | VU=${__VU} | ` +
            `status=400 | ` +
            `body=${response.body}`
        );

    } else if (response.status === 401) {

        status401.add(1);

        console.log(
            `UNAUTHORIZED | VU=${__VU} | ` +
            `status=401 | ` +
            `body=${response.body}`
        );

    } else if (response.status === 500) {

        status500.add(1);

        console.log(
            `SERVER_ERROR | VU=${__VU} | ` +
            `status=500 | ` +
            `body=${response.body}`
        );

    } else {

        otherStatus.add(1);

        console.log(
            `OTHER_STATUS | VU=${__VU} | ` +
            `status=${response.status} | ` +
            `body=${response.body}`
        );
    }

    // --------------------------------------------------------
    // Check
    // --------------------------------------------------------

    check(response, {
        "reservation request completed": (r) =>
            r.status === 201 || r.status === 409,
    });
}

// ============================================================
// FINAL SUMMARY
// ============================================================

export function handleSummary(data) {

    const metrics = data.metrics;

    const totalRequests =
        metrics.http_reqs?.values?.count || 0;

    const success =
        metrics.status_201?.values?.count || 0;

    const unavailable =
        metrics.status_409?.values?.count || 0;

    const badRequest =
        metrics.status_400?.values?.count || 0;

    const unauthorized =
        metrics.status_401?.values?.count || 0;

    const serverError =
        metrics.status_500?.values?.count || 0;

    const requestError =
        metrics.request_errors?.values?.count || 0;

    console.log("");
    console.log("========================================");
    console.log("       RESERVATION LOAD TEST");
    console.log("========================================");

    console.log(`Total Requests       : ${totalRequests}`);
    console.log(`Successful (201)     : ${success}`);
    console.log(`Unavailable (409)    : ${unavailable}`);
    console.log(`Bad Request (400)    : ${badRequest}`);
    console.log(`Unauthorized (401)   : ${unauthorized}`);
    console.log(`Server Error (500)   : ${serverError}`);
    console.log(`Request Errors       : ${requestError}`);

    console.log("========================================");
    console.log("Expected:");
    console.log("201 = Reservation successful");
    console.log("409 = Stock unavailable");
    console.log("401 = Authentication problem");
    console.log("400 = Bad request");
    console.log("500 = Backend error");
    console.log("========================================");
    console.log("");

    return {};
}
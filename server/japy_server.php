<?php
/**
 * JapyScript — PHP-compatible service gateway.
 *
 * Provides a drop-in HTTP entry point for JapyScript services that delegate
 * to PHP for host-integration (existing PHP applications calling .jpy
 * pipelines). This is a bridge layer, not the reference server.
 *
 * Requirements: PHP 8.1+ with the curl extension.
 */

declare(strict_types=1);

final class JapyGateway
{
    private string $runtimeUrl;
    private int $timeoutMs;

    public function __construct(
        string $runtimeUrl = 'http://127.0.0.1:8081',
        int $timeoutMs = 5000
    ) {
        $this->runtimeUrl = rtrim($runtimeUrl, '/');
        $this->timeoutMs  = $timeoutMs;
    }

    /**
     * Forward a request to the JapyScript runtime and return the raw response.
     */
    public function forward(string $method, string $path, array $headers, ?string $body): array
    {
        $url = $this->runtimeUrl . $path;
        $ch  = curl_init($url);

        $headerLines = [];
        foreach ($headers as $name => $value) {
            $headerLines[] = $name . ': ' . $value;
        }

        curl_setopt_array($ch, [
            CURLOPT_CUSTOMREQUEST  => strtoupper($method),
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER     => $headerLines,
            CURLOPT_TIMEOUT_MS     => $this->timeoutMs,
        ]);

        if ($body !== null && $body !== '') {
            curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
        }

        $response = curl_exec($ch);
        $status   = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        $error    = curl_error($ch);
        curl_close($ch);

        if ($response === false) {
            return ['status' => 502, 'body' => json_encode(['error' => $error])];
        }

        return ['status' => $status, 'body' => $response];
    }
}

// --------------------------------------------------------------------------
// Minimal front controller. Deploy behind a web server or run with:
//     php -S 0.0.0.0:8080 japy_server.php
// --------------------------------------------------------------------------

if (PHP_SAPI === 'cli-server') {
    $gateway = new JapyGateway();
    $headers = [];
    foreach (getallheaders() as $name => $value) {
        if (in_array(strtolower($name), ['host', 'connection', 'content-length'], true)) {
            continue;
        }
        $headers[$name] = $value;
    }

    $raw  = file_get_contents('php://input');
    $resp = $gateway->forward(
        $_SERVER['REQUEST_METHOD'],
        $_SERVER['REQUEST_URI'],
        $headers,
        $raw ?: null
    );

    http_response_code($resp['status']);
    header('Content-Type: application/json');
    echo $resp['body'];
    return true;
}

return new JapyGateway();

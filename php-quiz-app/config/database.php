<?php
function app_config(): array
{
    $file = __DIR__ . '/config.php';
    $local = file_exists($file) ? require $file : [];
    return [
        'db_host' => getenv('DB_HOST') ?: ($local['db_host'] ?? '127.0.0.1'),
        'db_port' => getenv('DB_PORT') ?: ($local['db_port'] ?? '3306'),
        'db_name' => getenv('DB_NAME') ?: ($local['db_name'] ?? 'online_quiz_php'),
        'db_user' => getenv('DB_USER') ?: ($local['db_user'] ?? 'quiz_user'),
        'db_password' => getenv('DB_PASSWORD') ?: ($local['db_password'] ?? 'quiz_password'),
        'openai_api_key' => getenv('OPENAI_API_KEY') ?: ($local['openai_api_key'] ?? ''),
        'openai_model' => getenv('OPENAI_MODEL') ?: ($local['openai_model'] ?? 'gpt-5-mini'),
    ];
}

function db(): PDO
{
    static $pdo = null;
    if ($pdo instanceof PDO) return $pdo;
    $c = app_config();
    $dsn = "mysql:host={$c['db_host']};port={$c['db_port']};dbname={$c['db_name']};charset=utf8mb4";
    $pdo = new PDO($dsn, $c['db_user'], $c['db_password'], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]);
    return $pdo;
}

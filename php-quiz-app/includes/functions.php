<?php
if (session_status() !== PHP_SESSION_ACTIVE) session_start();
require_once __DIR__ . '/../config/database.php';

function e(?string $value): string { return htmlspecialchars($value ?? '', ENT_QUOTES, 'UTF-8'); }
function redirect(string $page): never { header('Location: ' . $page); exit; }
function user(): ?array { return $_SESSION['user'] ?? null; }
function is_logged_in(): bool { return user() !== null; }
function is_staff(): bool { return in_array(user()['role'] ?? '', ['admin', 'teacher'], true); }
function require_login(): void { if (!is_logged_in()) redirect('login.php'); }
function require_staff(): void { if (!is_staff()) redirect('../login.php'); }
function flash(string $type, string $message): void { $_SESSION['flash'] = compact('type', 'message'); }
function get_flash(): ?array { $f = $_SESSION['flash'] ?? null; unset($_SESSION['flash']); return $f; }
function csrf_token(): string { if (empty($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(32)); return $_SESSION['csrf']; }
function csrf_field(): string { return '<input type="hidden" name="csrf" value="' . e(csrf_token()) . '">'; }
function verify_csrf(): void {
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && !hash_equals($_SESSION['csrf'] ?? '', $_POST['csrf'] ?? '')) {
        http_response_code(419); exit('Invalid request token. Please go back and try again.');
    }
}
function post(string $key): string { return trim($_POST[$key] ?? ''); }
function quiz_access_sql(string $alias = 'q'): array {
    if ((user()['role'] ?? '') === 'admin') return ['1=1', []];
    return ["{$alias}.created_by = ?", [user()['id']]];
}

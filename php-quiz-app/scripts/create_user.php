<?php
// Run: php scripts/create_user.php "Admin Name" admin@example.com Password123 admin
require_once __DIR__ . '/../config/database.php';
if (PHP_SAPI !== 'cli') exit("CLI only.\n");
[$script,$name,$email,$password,$role] = array_pad($argv,5,'');
if (!$name || !filter_var($email,FILTER_VALIDATE_EMAIL) || strlen($password)<8 || !in_array($role,['admin','teacher'],true)) {
    exit("Usage: php scripts/create_user.php \"Full Name\" email@example.com Password123 admin|teacher\n");
}
$s=db()->prepare('INSERT INTO users(name,email,password,role) VALUES(?,?,?,?) ON DUPLICATE KEY UPDATE name=VALUES(name),password=VALUES(password),role=VALUES(role)');
$s->execute([$name,strtolower($email),password_hash($password,PASSWORD_DEFAULT),$role]);
echo ucfirst($role)." account is ready.\n";

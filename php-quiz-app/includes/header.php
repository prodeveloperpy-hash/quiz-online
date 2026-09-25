<?php require_once __DIR__ . '/functions.php'; $pageTitle = $pageTitle ?? 'Quiz Online'; $flash = get_flash(); ?>
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title><?= e($pageTitle) ?> | Quiz Online</title><link rel="stylesheet" href="<?= str_contains($_SERVER['PHP_SELF'], '/admin/') ? '../' : '' ?>assets/css/style.css"></head>
<body><header class="site-header"><a class="brand" href="<?= is_staff() ? (str_contains($_SERVER['PHP_SELF'], '/admin/') ? 'index.php' : 'admin/index.php') : 'index.php' ?>">Quiz Online</a>
<nav>
<?php if (!is_logged_in()): ?><a href="index.php">Home</a><a href="login.php">Login</a><a class="button small" href="register.php">Register</a>
<?php elseif (is_staff()): ?><a href="<?= str_contains($_SERVER['PHP_SELF'], '/admin/') ? 'index.php' : 'admin/index.php' ?>">Admin</a><a href="<?= str_contains($_SERVER['PHP_SELF'], '/admin/') ? '../logout.php' : 'logout.php' ?>">Logout</a>
<?php else: ?><a href="dashboard.php">Dashboard</a><a href="categories.php">Quizzes</a><a href="profile.php">Profile</a><a href="logout.php">Logout</a><?php endif; ?>
</nav></header><main class="container">
<?php if ($flash): ?><div class="alert <?= e($flash['type']) ?>"><?= e($flash['message']) ?></div><?php endif; ?>

# Simple PHP Online Quiz System

A beginner-friendly quiz website made with plain HTML, CSS, JavaScript, PHP, and MySQL. Each screen has its own PHP file; common navigation, helpers, and database code are kept in small reusable files.

## Start with Docker (recommended)

1. Install and open Docker Desktop.
2. Open PowerShell in this `php-quiz-app` folder.
3. Run:

```powershell
docker compose up -d --build
```

4. Create the first admin account (change the example password):

```powershell
docker compose exec web php scripts/create_user.php "Main Admin" admin@example.com Admin123! admin
```

5. Open http://localhost:8080 and log in. Students can register themselves.

Create a teacher in the same way, using `teacher` as the last value:

```powershell
docker compose exec web php scripts/create_user.php "Teacher Name" teacher@example.com Teacher123! teacher
```

## AI quiz generator

Copy `.env.example` to `.env`, add an OpenAI API key, and restart the containers:

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

The API key stays on the server and is never sent to browser JavaScript. AI quizzes are always created as drafts so the teacher can review them before publishing. The integration uses the OpenAI Responses API with Structured Outputs.

## Important files

- `index.php` — landing page
- `login.php`, `register.php` — authentication
- `dashboard.php`, `categories.php`, `quiz.php`, `result.php`, `profile.php` — student pages
- `admin/` — teacher/admin pages
- `includes/` — shared header, footer, helpers, and AI function
- `config/database.php` — MySQL connection
- `database/schema.sql` — all database tables
- `assets/css/style.css` — complete design
- `assets/js/main.js` — quiz navigation and timer

## Without Docker

Use PHP 8.2+ with PDO MySQL and cURL, plus MySQL 8. Import `database/schema.sql`, copy `config/config.example.php` to `config/config.php`, edit the connection values, and serve the folder with Apache/XAMPP or `php -S localhost:8080`.

## Security notes

- Passwords use PHP `password_hash` and `password_verify`.
- SQL uses prepared statements.
- Forms use CSRF tokens.
- Do not commit `.env` or `config/config.php`.
- Rotate any SMTP/app password that has been shared in chat. This PHP version does not need SMTP credentials.

OpenAI API implementation follows the official [Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs) and [Responses API reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create).

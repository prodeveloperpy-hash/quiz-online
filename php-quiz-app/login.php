<?php
require_once 'includes/functions.php'; if(is_logged_in())redirect(is_staff()?'admin/index.php':'dashboard.php');$error='';
if($_SERVER['REQUEST_METHOD']==='POST'){verify_csrf();$email=strtolower(post('email'));$s=db()->prepare('SELECT id,name,email,password,role FROM users WHERE email=?');$s->execute([$email]);$u=$s->fetch();if($u&&password_verify($_POST['password']??'',$u['password'])){unset($u['password']);session_regenerate_id(true);$_SESSION['user']=$u;redirect(is_staff()?'admin/index.php':'dashboard.php');}$error='Email or password is incorrect.';}
$pageTitle='Login';require 'includes/header.php';?>
<form class="form-card" method="post"><h1>Login</h1><?php if($error):?><p class="error"><?=e($error)?></p><?php endif;?><?=csrf_field()?><label>Email</label><input type="email" name="email" required autofocus><label>Password</label><input type="password" name="password" required><br><br><button>Login</button><p>New student? <a href="register.php">Create an account</a></p></form>
<?php require 'includes/footer.php';?>

<?php
require_once 'includes/functions.php'; if (is_logged_in()) redirect(is_staff()?'admin/index.php':'dashboard.php');
$errors=[]; if($_SERVER['REQUEST_METHOD']==='POST'){verify_csrf();$name=post('name');$email=strtolower(post('email'));$password=$_POST['password']??'';
 if(strlen($name)<2)$errors[]='Please enter your full name.'; if(!filter_var($email,FILTER_VALIDATE_EMAIL))$errors[]='Enter a valid email.'; if(strlen($password)<8)$errors[]='Password must contain at least 8 characters.';
 if(!$errors){try{$s=db()->prepare("INSERT INTO users(name,email,password,role) VALUES(?,?,?,'student')");$s->execute([$name,$email,password_hash($password,PASSWORD_DEFAULT)]);flash('success','Account created. Please login.');redirect('login.php');}catch(PDOException $e){$errors[]=$e->getCode()==='23000'?'This email is already registered.':'Could not create account.';}}
}
$pageTitle='Register';require 'includes/header.php';?>
<form class="form-card" method="post"><h1>Create Account</h1><?php foreach($errors as $x):?><p class="error"><?=e($x)?></p><?php endforeach;?><?=csrf_field()?><label>Full Name</label><input name="name" value="<?=e($_POST['name']??'')?>" required><label>Email</label><input type="email" name="email" value="<?=e($_POST['email']??'')?>" required><label>Password</label><input type="password" name="password" minlength="8" required><p class="muted">Use at least 8 characters.</p><button>Create Account</button><p>Already registered? <a href="login.php">Login</a></p></form>
<?php require 'includes/footer.php';?>

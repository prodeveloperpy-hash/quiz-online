document.querySelectorAll('[data-confirm]').forEach(el=>el.addEventListener('click',e=>{if(!confirm(el.dataset.confirm))e.preventDefault()}));

const quizForm=document.getElementById('quiz-form');
if(quizForm){
 const questions=[...document.querySelectorAll('.question')], bar=document.querySelector('.progress span'), label=document.getElementById('question-number');
 let current=0, remaining=parseInt(quizForm.dataset.seconds||'0',10), timer=document.getElementById('timer');
 function show(i){current=Math.max(0,Math.min(i,questions.length-1));questions.forEach((q,n)=>q.classList.toggle('active',n===current));bar.style.width=((current+1)/questions.length*100)+'%';label.textContent=`Question ${current+1} of ${questions.length}`;document.getElementById('prev').disabled=current===0;document.getElementById('next').hidden=current===questions.length-1;document.getElementById('submit-quiz').hidden=current!==questions.length-1}
 document.getElementById('prev').onclick=()=>show(current-1);document.getElementById('next').onclick=()=>show(current+1);show(0);
 const tick=()=>{let m=Math.floor(remaining/60),s=remaining%60;timer.textContent=`${m}:${String(s).padStart(2,'0')}`;if(remaining--<=0){quizForm.submit();return}setTimeout(tick,1000)};tick();
}

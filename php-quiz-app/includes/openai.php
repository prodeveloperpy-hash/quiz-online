<?php
function generate_quiz_with_ai(string $topic, string $difficulty, int $count): array
{
    $config = app_config();
    if (!$config['openai_api_key']) throw new RuntimeException('OPENAI_API_KEY is not configured. Add it to docker-compose.yml or config/config.php.');
    if (!function_exists('curl_init')) throw new RuntimeException('PHP cURL extension is missing.');
    $schema = [
        'type'=>'object','properties'=>['title'=>['type'=>'string'],'description'=>['type'=>'string'],'questions'=>[
            'type'=>'array','items'=>['type'=>'object','properties'=>[
                'question'=>['type'=>'string'],
                'options'=>['type'=>'array','items'=>['type'=>'string'],'minItems'=>4,'maxItems'=>4],
                'correct_index'=>['type'=>'integer','minimum'=>0,'maximum'=>3],
            ],'required'=>['question','options','correct_index'],'additionalProperties'=>false],
        ]],'required'=>['title','description','questions'],'additionalProperties'=>false,
    ];
    $payload = [
        'model'=>$config['openai_model'],
        'input'=>[
            ['role'=>'developer','content'=>'Create accurate, unambiguous educational multiple-choice quizzes. Return exactly the requested number of questions and four distinct options per question.'],
            ['role'=>'user','content'=>"Create a {$difficulty} quiz about: {$topic}. It must contain exactly {$count} questions."],
        ],
        'text'=>['format'=>['type'=>'json_schema','name'=>'quiz','strict'=>true,'schema'=>$schema]],
        'store'=>false,
    ];
    $ch=curl_init('https://api.openai.com/v1/responses');curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_RETURNTRANSFER=>true,CURLOPT_TIMEOUT=>90,CURLOPT_HTTPHEADER=>['Authorization: Bearer '.$config['openai_api_key'],'Content-Type: application/json'],CURLOPT_POSTFIELDS=>json_encode($payload)]);$body=curl_exec($ch);$status=curl_getinfo($ch,CURLINFO_HTTP_CODE);$curlError=curl_error($ch);curl_close($ch);
    if($body===false)throw new RuntimeException('Could not contact OpenAI: '.$curlError);$response=json_decode($body,true);if($status>=400)throw new RuntimeException($response['error']['message']??'OpenAI request failed.');
    $text=$response['output_text']??'';if(!$text)foreach($response['output']??[] as $item)foreach($item['content']??[] as $content)if(($content['type']??'')==='output_text')$text.=$content['text']??'';
    $quiz=json_decode($text,true);if(!is_array($quiz)||count($quiz['questions']??[])!==$count)throw new RuntimeException('AI returned an incomplete quiz. Please try again.');return $quiz;
}

export type Role = 'admin' | 'teacher' | 'student'
export type User = {id:number; name:string; email:string; role:Role; roll_number?:string; department?:string; semester?:number; section?:string; is_active?:boolean}
export type Option = {id:number; text:string; is_correct?:boolean}
export type Question = {id:number; text:string; question_type:'mcq'|'short'; marks:number; options:Option[]}
export type Quiz = {id:number; title:string; description:string; department:string; semester:number; section:string; duration_minutes:number; starts_at:string; ends_at:string; status:string; creator_name:string; questions:Question[]}
export type Attempt = {id:number; quiz_id:number; quiz_title:string; student_name:string; status:string; objective_score:number; manual_score:number; total_score:number; total_marks:number; tab_violations:number; submission_reason?:string; retake_allowed:boolean}

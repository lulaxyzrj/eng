create table task (
	id bigint IDENTITY(1,1) NOT NULL,
	name varchar(60) COLLATE Latin1_General_CI_AI NULL,
	description varchar(100) COLLATE Latin1_General_CI_AI NULL,
	active bit NOT NULL,
)
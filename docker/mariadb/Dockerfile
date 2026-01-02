# MariaDB version: 11.8.3 ( Backend <-> DB/ETL 협의_26-01-02 )
FROM mariadb:11.8.3
# 팀 공통 설정
COPY my.cnf /etc/mysql/conf.d/99-team.cnf
# 초기화 스크립트
COPY initdb.d/ /docker-entrypoint-initdb.d/

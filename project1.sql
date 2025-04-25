USE projectdb;

-- 📦 1. 충전소 테이블
CREATE TABLE stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    statId VARCHAR(20) UNIQUE,
    statNm VARCHAR(100),
    addr TEXT,
    lat DOUBLE,
    lng DOUBLE,
    busiNm VARCHAR(100),
    year INT,
    zcode VARCHAR(10),
    zscode VARCHAR(10),
    useTime VARCHAR(100),
    parkingFree VARCHAR(5),
    limitYn VARCHAR(5),
    limitDetail TEXT,
    note TEXT,
    delYn VARCHAR(5),
    statUpdDt VARCHAR(30)
);

-- ⚡ 2. 충전기 테이블
CREATE TABLE chargers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    statId VARCHAR(20),
    chgerId VARCHAR(10),
    chgerType VARCHAR(10),
    stat VARCHAR(10),
    output DOUBLE,
    FOREIGN KEY (statId) REFERENCES stations(statId)
);

-- 📆 4. 연도별 전기차 등록 통계
CREATE TABLE ev_registered_yearly (
    id INT AUTO_INCREMENT PRIMARY KEY,
    zname VARCHAR(20),
    year INT,
    vehicle_count INT,
    UNIQUE (zname, year)
);

-- 🗺️ 5. 지역코드 맵핑
CREATE TABLE region_map (
    zcode INT PRIMARY KEY,
    zname VARCHAR(30) NOT NULL
);

-- 지역 데이터 삽입
INSERT INTO region_map (zcode, zname) VALUES
(11, '서울특별시'),
(26, '부산광역시'),
(27, '대구광역시'),
(28, '인천광역시'),
(29, '광주광역시'),
(30, '대전광역시'),
(31, '울산광역시'),
(36, '세종특별자치시'),
(41, '경기도'),
(42, '강원특별자치도'),
(43, '충청북도'),
(44, '충청남도'),
(45, '전라북도'),
(46, '전라남도'),
(47, '경상북도'),
(48, '경상남도'),
(50, '제주특별자치도');

-- 🔍 데이터 조회 쿼리 (샘플)
SELECT * FROM region_map ORDER BY zcode;
SELECT zcode, COUNT(*) FROM stations GROUP BY zcode;
SELECT year, zname, vehicle_count FROM ev_registered_yearly ORDER BY year DESC;

-- 📌 매핑되지 않은 zname 보정 (줄여쓴 지역명 → 정식명칭)
UPDATE ev_registered_yearly SET zname = '서울특별시' WHERE zname = '서울';
UPDATE ev_registered_yearly SET zname = '부산광역시' WHERE zname = '부산';
UPDATE ev_registered_yearly SET zname = '대구광역시' WHERE zname = '대구';
UPDATE ev_registered_yearly SET zname = '인천광역시' WHERE zname = '인천';
UPDATE ev_registered_yearly SET zname = '광주광역시' WHERE zname = '광주';
UPDATE ev_registered_yearly SET zname = '대전광역시' WHERE zname = '대전';
UPDATE ev_registered_yearly SET zname = '울산광역시' WHERE zname = '울산';
UPDATE ev_registered_yearly SET zname = '세종특별자치시' WHERE zname = '세종';
UPDATE ev_registered_yearly SET zname = '경기도' WHERE zname = '경기';
UPDATE ev_registered_yearly SET zname = '강원특별자치도' WHERE zname = '강원';
UPDATE ev_registered_yearly SET zname = '충청북도' WHERE zname = '충북';
UPDATE ev_registered_yearly SET zname = '충청남도' WHERE zname = '충남';
UPDATE ev_registered_yearly SET zname = '전라북도' WHERE zname = '전북';
UPDATE ev_registered_yearly SET zname = '전라남도' WHERE zname = '전남';
UPDATE ev_registered_yearly SET zname = '경상북도' WHERE zname = '경북';
UPDATE ev_registered_yearly SET zname = '경상남도' WHERE zname = '경남';
UPDATE ev_registered_yearly SET zname = '제주특별자치도' WHERE zname = '제주';

-- 중복 체크
SELECT DISTINCT zname FROM ev_registered_yearly ORDER BY zname;
SELECT * FROM region_map WHERE zname IN (
    SELECT DISTINCT zname FROM ev_registered_yearly
);

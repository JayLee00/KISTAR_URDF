last update: 2025-09-09

업데이트 내용:
모든 파트 기구학 완성
실제 간섭 되는 부분 각도는 확인 필요

-mass, inertia 측정 필요
-USD 파일 제작 필요

last update: 2025-09-10

업데이트 내용:
Thumb working range 수정
Fingertip 원점 및 회전 위치 수정
Little joint 0 회전 방향 수정
Joint 명 변경

last update: 2025-09-11

업데이트 내용:
1. usd 변환시 링크 사이에 충돌 이슈 해결 위해
    PIP, MCP, Fingertip -> lower, upper 쪼갬
    Palm -> front, back 쪼갬

2. joint의 mimic 기능 추가


last update: 2025-09-14

업데이트 내용:
1. MCP, PIP 튀어나온 부분 제거
2. Mass, Inertia 초기화
3. Bounding Box 처리 완료
비고: joint의 mimic 기능 추가 시 contact 될때 발산 하는 현상 발견 

last update: 2025-09-15

업데이트 내용:
1. Mass, Inertia 추가 완료
2. mimic joint 오류 해결 완료

last update: 2025-09-18

업데이트 내용:
1. thumb_base mass, inertia 변경

last update: 2025-12-14

업데이트 내용:
1. finger_tip 새로운 버전으로 업데이트
2. pip_lower finger, thumb 모두 wire case 추가, PIP 링크 수정 완료
3. 왼손 업데이트 완료
4. 엄지 Joint 2번 1303 으로 위치 변경
5. 20251214_KISTAR_SON_URDF_Bi/20251214_KISTAR_SON_URDF/ 경로에 URDF 및 USD 파일 있음.
meshes는 USD의 Visual, Colider 파일
KISTAR_SON_meshes 는 URDF의 STL 파일
USD 파일의 Colider는 관절부 충돌 방지를 위해 수정을 해 두었으므로 확인 요망.
각 관절마다 Torque 값을 늘려야지 원활한 손가락 제어 가능

last update: 2026-04-20

업데이트 내용:
1. 엄지 cmc joint 한 점에서 만나게 base 설정
2. 좌 우 핸드 대칭으로 움직이게 설정
3. 목업 fixed joint 로 추가 완료 (front및 back 파트가 목업임임)
4. link 이름 통일 "right_hand_middle_2_(front)_link"

last update: 2026-04-28
1. 엄지 joint_2번 오른손 기준 바깥쪽으로 돌게 수정 후 좌우 대칭.
2. 이너시아  대각 행렬 만 살려서 symtric 하게 변경

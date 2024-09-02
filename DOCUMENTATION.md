# 프론트엔드 개발자를 위한 백엔드 API 문서

## API 엔드포인트

### 인증 (Authentication)
#### 로그인
- **URL**: `/auth/token`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "username": "user@example.com",
    "password": "password"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "string",
    "refresh_token": "string",
    "token_type": "bearer"
  }
  ```
- **설명**: 사용자가 로그인하여 액세스 토큰과 리프레시 토큰을 발급받습니다.


```18:39:saveplate/routers/auth.py
@router.post("/token", response_model=TokenPair)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    사용자 로그인을 처리하고 액세스 토큰과 리프레시 토큰을 발급합니다.

    Args:
        form_data (OAuth2PasswordRequestForm): 사용자 이름과 비밀번호를 포함한 폼 데이터

    Returns:
        TokenPair: 액세스 토큰과 리프레시 토큰

    Raises:
        HTTPException: 인증 실패 시 401 Unauthorized 에러 발생
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_token_pair(user.email)
```


#### 리프레시 토큰
- **URL**: `/auth/refresh`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "refresh_token": "string"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "string",
    "refresh_token": "string",
    "token_type": "bearer"
  }
  ```
- **설명**: 리프레시 토큰을 사용하여 새로운 액세스 토큰과 리프레시 토큰을 발급받습니다.


```41:62:saveplate/routers/auth.py
@router.post("/refresh", response_model=TokenPair)
def refresh_token(refresh_token: str):
    """
    리프레시 토큰을 사용하여 새로운 액세스 토큰과 리프레시 토큰을 발급합니다.

    Args:
        refresh_token (str): 유효한 리프레시 토큰

    Returns:
        TokenPair: 새로운 액세스 토큰과 리프레시 토큰

    Raises:
        HTTPException: 유효하지 않은 리프레시 토큰일 경우 401 Unauthorized 에러 발생
    """
    user = get_user_by_refresh_token(refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_token_pair(user.email)
```


#### 회원가입
- **URL**: `/auth/register`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "password",
    "name": "John Doe",
    "gender": "male",
    "birth_date": "1990-01-01"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "string",
    "refresh_token": "string",
    "token_type": "bearer"
  }
  ```
- **설명**: 새로운 사용자를 등록하고 액세스 토큰과 리프레시 토큰을 발급받습니다.


```64:90:saveplate/routers/auth.py
@router.post("/register", response_model=TokenPair)
def register_user(user_data: UserCreate):
    """
    새로운 사용자를 등록하고 액세스 토큰과 리프레시 토큰을 발급합니다.

    Args:
        user_data (UserCreate): 새 사용자의 정보 (이메일, 비밀번호, 이름, 성별, 생년월일)

    Returns:
        TokenPair: 새로 생성된 사용자의 액세스 토큰과 리프레시 토큰

    Raises:
        HTTPException: 사용자 생성 실패 시 500 Internal Server Error 발생
    """
    try:
        user = create_user(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name,
            gender=user_data.gender,
            birth_date=user_data.birth_date
        )
        return create_token_pair(user.email)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
```


### 사용자 (User)
#### 재료 목록 조회
- **URL**: `/user/ingredients`
- **Method**: `GET`
- **Headers**:
  ```json
  {
    "Authorization": "Bearer access_token"
  }
  ```
- **Response**:
  ```json
  [
    {
      "name": "Tomato",
      "amount": 5
    },
    ...
  ]
  ```
- **설명**: 사용자가 가지고 있는 재료 목록을 조회합니다.


```18:45:saveplate/routers/user.py
@router.get("/ingredients")
@transactional("read")
def my_ingredients(
    tx: ManagedTransaction,
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    사용자의 재료 목록을 조회합니다.

    Returns:
        List[Dict[str, Any]]: 사용자가 가지고 있는 재료 목록
    """
    try:
        result = tx.run("""
            MATCH (u:User)-[r:HAS]->(i) WHERE u.email=$user_email RETURN i, r.amount
        """, user_email=current_user.email)

        ingredients = []
        for record in result:
            ingredient = dict(record["i"])
            ingredient["amount"] = record["r.amount"]
            if "birth_date" in ingredient and isinstance(ingredient["birth_date"], neo4j.time.Date):
                ingredient["birth_date"] = date.fromisoformat(str(ingredient["birth_date"]))
            if "join_date" in ingredient and isinstance(ingredient["join_date"], neo4j.time.Date):
                ingredient["join_date"] = date.fromisoformat(str(ingredient["join_date"]))
            ingredients.append(ingredient)

        return ingredients
```


#### 재료 추가
- **URL**: `/user/ingredient`
- **Method**: `POST`
- **Headers**:
  ```json
  {
    "Authorization": "Bearer access_token"
  }
  ```
- **Request Body**:
  ```json
  {
    "ingredients": [
      {
        "name": "Tomato",
        "amount": 5
      }
    ]
  }
  ```
- **Response**:
  ```json
  [
    {
      "user": {
        "email": "user@example.com",
        ...
      },
      "ingredient": {
        "name": "Tomato",
        ...
      },
      "amount": 5
    },
    ...
  ]
  ```
- **설명**: 사용자의 재료를 추가합니다.


```50:95:saveplate/routers/user.py
@router.post("/ingredient")
@transactional("write")
def add_ingredient(
    tx: ManagedTransaction,
    req: AddUserIngredient,
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    사용자의 재료를 추가합니다.

    Args:
        req (AddUserIngredient): 추가할 재료 목록

    Returns:
        List[Dict[str, Any]]: 추가된 사용자와 재료 정보
    """
    try:
        ingredients = req.ingredients
        user_result = tx.run("""
            UNWIND $ingredients AS e
            MATCH (u:User {email: $user_email})
            MATCH (i:Ingredient {name: e.name})
            MERGE (u)-[r:HAS]->(i)
            ON CREATE SET r.amount = e.amount
            ON MATCH SET r.amount = r.amount + e.amount
            RETURN u, i, r.amount AS amount
        """, user_email=current_user.email, ingredients=[ing.model_dump() for ing in ingredients])
        
        result = []
        for record in user_result:
            user_data = dict(record["u"])
            ingredient_data = dict(record["i"])
            if "birth_date" in user_data and isinstance(user_data["birth_date"], neo4j.time.Date):
                user_data["birth_date"] = date.fromisoformat(str(user_data["birth_date"]))
            if "join_date" in user_data and isinstance(user_data["join_date"], neo4j.time.Date):
                user_data["join_date"] = date.fromisoformat(str(user_data["join_date"]))
            result.append({
                "user": user_data,
                "ingredient": ingredient_data,
                "amount": record["amount"]
            })

        return result
    except Exception as e:
        logger.error(f"Error in add_ingredient: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Internal server error")
```


### 레시피 (Recipes)
#### 가능한 레시피 조회
- **URL**: `/user/recipes`
- **Method**: `GET`
- **Headers**:
  ```json
  {
    "Authorization": "Bearer access_token"
  }
  ```
- **Response**:
  ```json
  [
    {
      "food": "Pasta",
      "recipe": "Tomato Pasta",
      "sim": 0.9
    },
    ...
  ]
  ```
- **설명**: 사용자가 가진 재료로 만들 수 있는 레시피를 조회합니다.


```97:121:saveplate/routers/user.py
# 주석 처리된 쿼리는 함수로 구현하지 않았지만, 필요하다면 다음과 같이 구현할 수 있습니다:
@router.get("/recipes")
@transactional("read")
def get_available_recipes(
    tx: ManagedTransaction,
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    try:
        result = tx.run('''
        MATCH (u:User {email: $user_email})-[:HAS]->(i)
        WHERE labels(i)[0] IN ['Ingredient', 'Sauce']
        WITH collect(i.name) AS A
        MATCH (i)-[]->(r:Recipe)-[:RECIPE_OF]->(f:Food)
        WITH A, f, r, collect(i.name) AS R 
        WITH *, apoc.coll.intersection(A, R) AS X
        WHERE size(X) <> 0
        WITH *, size(apoc.coll.intersection(X, R)) AS i, size(apoc.coll.union(X, R)) AS u
        WHERE u <> 0
        WITH f.name AS food, r.name AS recipe, i/toFloat(u) AS sim
        RETURN food, recipe, sim ORDER BY sim DESC
        ''', user_email=current_user.email)
        return result.data()
    except Exception as e:
        logger.error(f"Error in get_available_recipes: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Internal server error")
```


### 자동완성 (Autocompletion)
#### 재료 및 소스 자동완성
- **URL**: `/autocompletion`
- **Method**: `GET`
- **Query Parameters**:
  - `type`: `ingredient` 또는 `sauce`
  - `data`: 검색할 문자열
  - `limit`: 반환할 결과의 최대 개수 (기본값: 10)
- **Response**:
  ```json
  [
    "Tomato",
    "Tomato Sauce",
    ...
  ]
  ```
- **설명**: 재료나 소스 이름의 자동완성 결과를 제공합니다.


```17:39:saveplate/routers/autocompletion.py
@router.get("")
@lru_with_ttl(ttl_seconds=60*10)
@transactional("read")
def autocompletion(tx: ManagedTransaction, type: AutoCompletionType, data: str, limit: int = 10) -> list[str]:
    """
    재료나 소스 이름의 자동완성 결과를 제공합니다.

    Args:
        type (AutoCompletionType): "ingredient" 또는 "sauce"
        data (str): 검색할 문자열
        limit (int, optional): 반환할 결과의 최대 개수. 기본값은 10.

    Returns:
        list[str]: 자동완성된 이름 목록
    """
    try:
        t = type.capitalize()
        result = tx.run(f'match (n: {t}) where n.name starts with $prefix return n.name as name order by n.popularity desc limit $limit', prefix=data, limit=limit)
        names = result.value(key="name")
        return names
    except Exception as e:
        logger.error(f"Error in autocompletion: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```


## 인증 및 권한
모든 보호된 엔드포인트는 `Authorization` 헤더에 `Bearer` 토큰을 포함해야 합니다. 토큰은 로그인 또는 회원가입 시 발급됩니다.

## 예제 코드
### 로그인 예제
```python
import requests

url = "http://localhost:8000/auth/token"
data = {
    "username": "user@example.com",
    "password": "password"
}
response = requests.post(url, data=data)
print(response.json())
```

### 재료 목록 조회 예제
```python
import requests

url = "http://localhost:8000/user/ingredients"
headers = {
    "Authorization": "Bearer access_token"
}
response = requests.get(url, headers=headers)
print(response.json())
```
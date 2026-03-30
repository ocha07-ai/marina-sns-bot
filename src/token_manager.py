"""
token_manager.py - Threads アクセストークンの自動更新を管理する

長期トークン（60日）を期限切れ前に自動更新し、.env に書き戻す。
投稿のたびに呼び出すことで実質無期限に運用できる。
"""
import base64
import json
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

BASE_DIR       = os.path.dirname(os.path.dirname(__file__))
TOKEN_INFO_PATH = os.path.join(BASE_DIR, "data", "token_info.json")
ENV_PATH        = os.path.join(BASE_DIR, ".env")
REFRESH_THRESHOLD_DAYS = 30   # 残り30日以内になったら更新


def _load_token_info() -> dict:
    """token_info.json を読み込む。なければ空dictを返す。"""
    if os.path.exists(TOKEN_INFO_PATH):
        with open(TOKEN_INFO_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_token_info(info: dict):
    """token_info.json に保存する。"""
    os.makedirs(os.path.dirname(TOKEN_INFO_PATH), exist_ok=True)
    with open(TOKEN_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)


def _encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    """
    GitHub Secrets API 用に libsodium SealedBox でシークレットを暗号化する。
    PyNaCl (PyNaCl>=1.5.0) が必要。
    """
    from nacl import encoding, public  # PyNaCl

    public_key_bytes = base64.b64decode(public_key_b64)
    sealed_box = public.SealedBox(public.PublicKey(public_key_bytes))
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def _update_github_secret(new_token: str):
    """
    GitHub Secrets REST API を使って THREADS_ACCESS_TOKEN を更新する。
    環境変数 GH_TOKEN (secrets:write スコープの PAT) と
    GH_REPO (owner/repo 形式) が必要。
    """
    gh_token = os.environ.get("GH_TOKEN", "")
    gh_repo  = os.environ.get("GH_REPO", "")
    if not gh_token or not gh_repo:
        return  # ローカル実行時はスキップ

    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    base_url = f"https://api.github.com/repos/{gh_repo}/actions/secrets"

    r = requests.get(f"{base_url}/public-key", headers=headers, timeout=10)
    if not r.ok:
        print(f"[TokenManager] GitHub公開鍵取得失敗: {r.status_code} {r.text}")
        return

    key_data = r.json()
    encrypted_value = _encrypt_secret(key_data["key"], new_token)

    r2 = requests.put(
        f"{base_url}/THREADS_ACCESS_TOKEN",
        headers=headers,
        json={"encrypted_value": encrypted_value, "key_id": key_data["key_id"]},
        timeout=10,
    )
    if r2.ok:
        print("[TokenManager] GitHub Secret 'THREADS_ACCESS_TOKEN' を更新しました")
    else:
        print(f"[TokenManager] GitHub Secret更新失敗: {r2.status_code} {r2.text}")


def _update_env(new_token: str):
    """
    トークンを新しい値に更新する。
    - 常に: 実行中の os.environ を即時更新
    - ローカル: .env ファイルに書き戻す
    - GitHub Actions: GitHub Secrets API でシークレットを更新
    """
    os.environ["THREADS_ACCESS_TOKEN"] = new_token

    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding="utf-8") as f:
            lines = f.readlines()
        updated = []
        for line in lines:
            if line.startswith("THREADS_ACCESS_TOKEN="):
                updated.append(f"THREADS_ACCESS_TOKEN={new_token}\n")
            else:
                updated.append(line)
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(updated)

    _update_github_secret(new_token)


def _refresh_token(current_token: str) -> tuple[str, datetime] | None:
    """
    Threads API でトークンを更新する。

    Returns:
        (新トークン, 新有効期限) または失敗時 None
    """
    try:
        r = requests.get(
            "https://graph.threads.net/refresh_access_token",
            params={
                "grant_type": "th_refresh_token",
                "access_token": current_token,
            },
            timeout=10,
        )
        if not r.ok:
            print(f"[TokenManager] 更新失敗: {r.status_code} {r.text}")
            return None

        data       = r.json()
        new_token  = data["access_token"]
        expires_in = data.get("expires_in", 5184000)  # デフォルト60日
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        return new_token, expires_at

    except Exception as e:
        print(f"[TokenManager] 更新エラー: {e}")
        return None


def ensure_valid_token() -> bool:
    """
    Threads トークンの有効期限を確認し、必要なら自動更新する。
    投稿前に呼び出すこと。

    Returns:
        True: トークンが有効（または更新成功）
        False: 更新失敗（投稿を中止すべき）
    """
    load_dotenv(override=True)
    current_token = os.environ.get("THREADS_ACCESS_TOKEN", "")
    if not current_token:
        print("[TokenManager] THREADS_ACCESS_TOKEN が未設定です")
        return False

    info       = _load_token_info()
    expires_at = None

    if "threads_token_expires_at" in info:
        expires_at = datetime.fromisoformat(info["threads_token_expires_at"])

    # 有効期限が未記録 → 初回セットアップとして即時更新して記録
    if expires_at is None:
        print("[TokenManager] 有効期限が未記録のため初回更新を実行します")
        result = _refresh_token(current_token)
        if result:
            new_token, expires_at = result
            _update_env(new_token)
            _save_token_info({"threads_token_expires_at": expires_at.isoformat()})
            days_left = (expires_at - datetime.now()).days
            print(f"[TokenManager] トークン更新完了（有効期限: {expires_at.strftime('%Y-%m-%d')}、残り{days_left}日）")
        return result is not None

    days_left = (expires_at - datetime.now()).days

    # 残り30日以内なら更新
    if days_left <= REFRESH_THRESHOLD_DAYS:
        print(f"[TokenManager] 残り{days_left}日のため自動更新します")
        result = _refresh_token(current_token)
        if result:
            new_token, new_expires_at = result
            _update_env(new_token)
            _save_token_info({"threads_token_expires_at": new_expires_at.isoformat()})
            new_days = (new_expires_at - datetime.now()).days
            print(f"[TokenManager] 更新完了（新有効期限: {new_expires_at.strftime('%Y-%m-%d')}、残り{new_days}日）")
            return True
        else:
            print(f"[TokenManager] 更新失敗。残り{days_left}日で期限切れになります")
            return days_left > 0  # まだ有効なら続行

    print(f"[TokenManager] トークン有効（有効期限: {expires_at.strftime('%Y-%m-%d')}、残り{days_left}日）")
    return True

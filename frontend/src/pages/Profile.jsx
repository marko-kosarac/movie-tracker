import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

import bg from "../assets/profile-pic3.jpg";

import avatar0 from "../assets/avatars/default.png";
import avatar1 from "../assets/avatars/boy.png";
import avatar2 from "../assets/avatars/boy2.png";
import avatar3 from "../assets/avatars/boy3.png";
import avatar4 from "../assets/avatars/boy4.png";
import avatar5 from "../assets/avatars/boy5.png";
import avatar6 from "../assets/avatars/girl.png";
import avatar7 from "../assets/avatars/girl2.png";
import avatar8 from "../assets/avatars/girl3.png";
import avatar9 from "../assets/avatars/girl4.png";
import avatar10 from "../assets/avatars/girl5.png";

const avatarMap = {
  avatar0,
  avatar1,
  avatar2,
  avatar3,
  avatar4,
  avatar5,
  avatar6,
  avatar7,
  avatar8,
  avatar9,
  avatar10,
};

const avatarOptions = [
  "avatar0",
  "avatar1",
  "avatar2",
  "avatar3",
  "avatar4",
  "avatar5",
  "avatar6",
  "avatar7",
  "avatar8",
  "avatar9",
  "avatar10",
];

function Profile() {
  const { user, setUser } = useAuth();

  const [avatar, setAvatar] = useState("avatar0");
  const [selectedAvatar, setSelectedAvatar] = useState("avatar0");

  const [showAvatarDialog, setShowAvatarDialog] = useState(false);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (user?.avatar && avatarMap[user.avatar]) {
      setAvatar(user.avatar);
      setSelectedAvatar(user.avatar);
    } else {
      setAvatar("avatar0");
      setSelectedAvatar("avatar0");
    }
  }, [user]);

  async function saveAvatar() {
    const token = localStorage.getItem("token");

    try {
      const response = await fetch("http://127.0.0.1:8000/auth/avatar", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          avatar: selectedAvatar,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Avatar update failed");
      }

      setAvatar(data.avatar);
      setSelectedAvatar(data.avatar);
      setUser(data);
      setShowAvatarDialog(false);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handlePasswordChange(e) {
    e.preventDefault();
    setError("");
    setMessage("");

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    const token = localStorage.getItem("token");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/auth/change-password",
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            new_password: newPassword,
            confirm_password: confirmPassword,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Password change failed");
      }

      setMessage("Password changed successfully");
      setNewPassword("");
      setConfirmPassword("");

      setTimeout(() => {
        setShowPasswordDialog(false);
        setMessage("");
      }, 800);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="profile-page" style={{ backgroundImage: `url(${bg})` }}>
      <div className="profile-card-centered compact-profile-card">
        <div className="avatar-wrapper profile-main-avatar">
          <img
            src={avatarMap[avatar] || avatarMap.avatar0}
            alt="avatar"
            className="profile-avatar-img"
          />

          <button
            className="edit-avatar-button"
            onClick={() => {
              setSelectedAvatar(avatar);
              setShowAvatarDialog(true);
              setError("");
            }}
          >
            ✎
          </button>
        </div>

        <h1 className="profile-username">{user?.username}</h1>

        <p className="profile-email">{user?.email}</p>

        <button
          className="small-password-button"
          onClick={() => {
            setShowPasswordDialog(true);
            setError("");
            setMessage("");
          }}
        >
          Change password
        </button>
      </div>

      {showAvatarDialog && (
        <div className="modal-backdrop">
          <div className="password-modal">
            <button
              className="modal-close"
              onClick={() => setShowAvatarDialog(false)}
            >
              ×
            </button>

            <h2>Choose avatar</h2>

            <div className="avatar-picker modal-avatar-picker">
              {avatarOptions.map((item) => (
                <button
                  key={item}
                  className={
                    selectedAvatar === item
                      ? "avatar-image-option active"
                      : "avatar-image-option"
                  }
                  onClick={() => setSelectedAvatar(item)}
                >
                  <img src={avatarMap[item]} alt="avatar option" />
                </button>
              ))}
            </div>

            {error && <p className="error-text">{error}</p>}

            <div className="modal-actions">
              <button onClick={saveAvatar}>Save</button>
              <button
                className="cancel-button"
                onClick={() => setShowAvatarDialog(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {showPasswordDialog && (
        <div className="modal-backdrop">
          <div className="password-modal">
            <button
              className="modal-close"
              onClick={() => setShowPasswordDialog(false)}
            >
              ×
            </button>

            <h2>Change password</h2>

            <form onSubmit={handlePasswordChange}>
              <div className="form-group">
                <label>New password</label>
                <input
                  type="password"
                  placeholder="Enter new password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Confirm password</label>
                <input
                  type="password"
                  placeholder="Repeat new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>

              {error && <p className="error-text">{error}</p>}
              {message && <p className="success-text">{message}</p>}

              <button disabled={!newPassword || !confirmPassword}>
                Save password
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Profile;
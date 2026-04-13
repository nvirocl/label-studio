import { useCallback, useContext, useEffect, useState } from "react";
import { Button, Userpic } from "@humansignal/ui";
import { ProjectContext } from "../../providers/ProjectProvider";
import { useAPI } from "../../providers/ApiProvider";
import { cn } from "../../utils/bem";
import { Spinner } from "../../components";
import { useCurrentUserRole } from "../Organization/PeoplePage/useCurrentUserRole";
import "./MembersSettings.prefix.css";

export const MembersSettings = () => {
  const { project } = useContext(ProjectContext);
  const api = useAPI();
  const { canManageRoles } = useCurrentUserRole();
  const [members, setMembers] = useState([]);
  const [orgMembers, setOrgMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [saving, setSaving] = useState(false);

  const fetchMembers = useCallback(async () => {
    if (!project?.id) return;
    try {
      const response = await api.callApi("projectMembers", {
        params: { pk: project.id },
      });
      setMembers(Array.isArray(response) ? response : response?.results || []);
    } catch (err) {
      console.error("Failed to fetch project members:", err);
    }
  }, [api, project?.id]);

  const fetchOrgMembers = useCallback(async () => {
    try {
      const response = await api.callApi("memberships", {
        params: { pk: 1, page_size: -1 },
      });
      if (response?.results) {
        setOrgMembers(response.results);
      }
    } catch (err) {
      console.error("Failed to fetch org members:", err);
    }
  }, [api]);

  useEffect(() => {
    Promise.all([fetchMembers(), fetchOrgMembers()]).finally(() => setLoading(false));
  }, [fetchMembers, fetchOrgMembers]);

  const handleAddMember = useCallback(async () => {
    if (!selectedUserId || !project?.id) return;
    setSaving(true);
    try {
      await api.callApi("addProjectMember", {
        params: { pk: project.id },
        body: { user_id: Number(selectedUserId) },
      });
      setSelectedUserId("");
      await fetchMembers();
    } catch (err) {
      console.error("Failed to add member:", err);
    } finally {
      setSaving(false);
    }
  }, [api, project?.id, selectedUserId, fetchMembers]);

  const handleRemoveMember = useCallback(
    async (userId) => {
      if (!project?.id) return;
      setSaving(true);
      try {
        await api.callApi("removeProjectMember", {
          params: { pk: project.id, userPk: userId },
        });
        await fetchMembers();
      } catch (err) {
        console.error("Failed to remove member:", err);
      } finally {
        setSaving(false);
      }
    },
    [api, project?.id, fetchMembers],
  );

  const memberIds = new Set(members.map((m) => m.id));
  const availableMembers = orgMembers.filter(({ user }) => !memberIds.has(user.id));

  if (loading) {
    return (
      <div className={cn("members-settings").toClassName()}>
        <Spinner size={36} />
      </div>
    );
  }

  return (
    <div className={cn("members-settings").toClassName()}>
      <h1>Members</h1>
      <p className={cn("members-settings").elem("description").toClassName()}>
        Manage which users have access to this project. Annotators and Reviewers can only see projects they are assigned
        to.
      </p>

      {canManageRoles && (
        <div className={cn("members-settings").elem("add-form").toClassName()}>
          <select
            className="rounded-base border border-neutral-border bg-neutral-surface px-base py-tight text-body-medium"
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
            disabled={saving}
          >
            <option value="">Select a user to add...</option>
            {availableMembers.map(({ user, role }) => (
              <option key={user.id} value={user.id}>
                {user.first_name} {user.last_name} ({user.email})
              </option>
            ))}
          </select>
          <Button onClick={handleAddMember} disabled={!selectedUserId || saving} look="primary">
            {saving ? "Adding..." : "Add Member"}
          </Button>
        </div>
      )}

      <div className={cn("members-settings").elem("list").toClassName()}>
        {members.length === 0 ? (
          <p className={cn("members-settings").elem("empty").toClassName()}>
            No members assigned to this project yet.
          </p>
        ) : (
          members.map((user) => (
            <div key={user.id} className={cn("members-settings").elem("member").toClassName()}>
              <div className={cn("members-settings").elem("member-info").toClassName()}>
                <Userpic user={user} style={{ width: 32, height: 32 }} />
                <div>
                  <div className={cn("members-settings").elem("member-name").toClassName()}>
                    {user.first_name} {user.last_name}
                  </div>
                  <div className={cn("members-settings").elem("member-email").toClassName()}>{user.email}</div>
                </div>
              </div>
              {canManageRoles && (
                <Button look="danger" onClick={() => handleRemoveMember(user.id)} disabled={saving}>
                  Remove
                </Button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

MembersSettings.title = "Members";
MembersSettings.path = "/members";

import { format } from "date-fns";
import { useCallback, useState } from "react";
import { NavLink } from "react-router-dom";
import { IconCross } from "@humansignal/icons";
import { Userpic, Button } from "@humansignal/ui";
import { cn } from "../../../utils/bem";
import { useAPI } from "../../../providers/ApiProvider";
import { RoleBadge, ROLE_LABELS } from "./RoleBadge";
import { useCurrentUserRole } from "./useCurrentUserRole";
import "./SelectedUser.prefix.css";

const ASSIGNABLE_ROLES = [
  { code: "AD", name: "Administrator" },
  { code: "MA", name: "Manager" },
  { code: "RE", name: "Reviewer" },
  { code: "AN", name: "Annotator" },
  { code: "NO", name: "Not Activated" },
  { code: "DI", name: "Deactivated" },
];

const UserProjectsLinks = ({ projects }) => {
  return (
    <div className={cn("user-info").elem("links-list").toClassName()}>
      {projects.map((project) => (
        <NavLink
          className={cn("user-info").elem("project-link").toClassName()}
          key={`project-${project.id}`}
          to={`/projects/${project.id}`}
          data-external
        >
          {project.title}
        </NavLink>
      ))}
    </div>
  );
};

export const SelectedUser = ({ user, onClose, onRoleChanged }) => {
  const api = useAPI();
  const [role, setRole] = useState(user.role);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const { canManageRoles } = useCurrentUserRole();
  const isOwner = role === "OW";

  const handleRoleChange = useCallback(
    async (e) => {
      const newRole = e.target.value;
      setSaving(true);
      setError(null);

      try {
        const response = await api.callApi("updateMemberRole", {
          params: {
            pk: user.active_organization,
            userPk: user.id,
          },
          body: { role: newRole },
        });

        if (response?.role) {
          setRole(response.role);
          onRoleChanged?.(user.id, response.role);
        }
      } catch (err) {
        setError(err?.message || "Failed to update role");
      } finally {
        setSaving(false);
      }
    },
    [api, user.id, user.active_organization, onRoleChanged],
  );

  const fullName = [user.first_name, user.last_name]
    .filter((n) => !!n)
    .join(" ")
    .trim();

  return (
    <div className={cn("user-info").toClassName()}>
      <Button
        look="string"
        onClick={onClose}
        className="absolute top-[20px] right-[24px]"
        aria-label="Close user details"
      >
        <IconCross />
      </Button>

      <div className={cn("user-info").elem("header").toClassName()}>
        <Userpic user={user} style={{ width: 64, height: 64, fontSize: 28 }} />
        <div className={cn("user-info").elem("info-wrapper").toClassName()}>
          {fullName && <div className={cn("user-info").elem("full-name").toClassName()}>{fullName}</div>}
          <p className={cn("user-info").elem("email").toClassName()}>{user.email}</p>
        </div>
      </div>

      <div className={cn("user-info").elem("section").toClassName()}>
        <div className={cn("user-info").elem("section-title").toClassName()}>Role</div>
        {canManageRoles && !isOwner ? (
          <div className="flex flex-col gap-tight">
            <select
              className="w-full rounded-base border border-neutral-border bg-neutral-surface px-base py-tight text-body-medium"
              value={role}
              onChange={handleRoleChange}
              disabled={saving}
              aria-label="Change user role"
            >
              {ASSIGNABLE_ROLES.map((r) => (
                <option key={r.code} value={r.code}>
                  {r.name}
                </option>
              ))}
            </select>
            {saving && <span className="text-body-small text-neutral-content-subtlest">Saving...</span>}
            {error && <span className="text-body-small text-negative-content">{error}</span>}
          </div>
        ) : (
          <RoleBadge role={role} />
        )}
      </div>

      {user.phone && (
        <div className={cn("user-info").elem("section").toClassName()}>
          <a href={`tel:${user.phone}`}>{user.phone}</a>
        </div>
      )}

      {!!user.created_projects?.length && (
        <div className={cn("user-info").elem("section").toClassName()}>
          <div className={cn("user-info").elem("section-title").toClassName()}>Created Projects</div>

          <UserProjectsLinks projects={user.created_projects} />
        </div>
      )}

      {!!user.contributed_to_projects?.length && (
        <div className={cn("user-info").elem("section").toClassName()}>
          <div className={cn("user-info").elem("section-title").toClassName()}>Contributed to</div>

          <UserProjectsLinks projects={user.contributed_to_projects} />
        </div>
      )}

      <p className={cn("user-info").elem("last-active").toClassName()}>
        Last activity on: {format(new Date(user.last_activity), "dd MMM yyyy, KK:mm a")}
      </p>
    </div>
  );
};

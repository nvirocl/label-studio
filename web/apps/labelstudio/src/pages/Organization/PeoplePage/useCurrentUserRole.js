import { useCallback, useEffect, useState } from "react";
import { useAPI } from "../../../providers/ApiProvider";

export const useCurrentUserRole = () => {
  const api = useAPI();
  const [role, setRole] = useState(null);

  useEffect(() => {
    const fetchRole = async () => {
      try {
        const response = await api.callApi("me");

        if (response?.org_role) {
          setRole(response.org_role);
        }
      } catch {
        // Silently fail - role features will be hidden
      }
    };

    fetchRole();
  }, [api]);

  const canManageRoles = role === "OW" || role === "AD";

  return { role, canManageRoles };
};

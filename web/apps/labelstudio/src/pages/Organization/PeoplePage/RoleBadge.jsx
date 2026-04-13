const ROLE_LABELS = {
  OW: "Owner",
  AD: "Administrator",
  MA: "Manager",
  RE: "Reviewer",
  AN: "Annotator",
  NO: "Not Activated",
  DI: "Deactivated",
};

const ROLE_COLORS = {
  OW: { bg: "bg-negative-surface", text: "text-negative-content" },
  AD: { bg: "bg-primary-surface", text: "text-primary-content" },
  MA: { bg: "bg-positive-surface", text: "text-positive-content" },
  RE: { bg: "bg-warning-surface", text: "text-warning-content" },
  AN: { bg: "bg-neutral-surface", text: "text-neutral-content" },
  NO: { bg: "bg-neutral-surface", text: "text-neutral-content-subtlest" },
  DI: { bg: "bg-neutral-surface", text: "text-neutral-content-subtlest" },
};

export const RoleBadge = ({ role }) => {
  const label = ROLE_LABELS[role] || role;
  const colors = ROLE_COLORS[role] || ROLE_COLORS.AN;

  return (
    <span
      className={`inline-flex items-center px-tight py-tighter rounded-base text-body-small font-medium ${colors.bg} ${colors.text}`}
    >
      {label}
    </span>
  );
};

export { ROLE_LABELS };

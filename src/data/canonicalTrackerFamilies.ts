import {
  CANONICAL_TRACKER_FAMILIES,
  HOMEPAGE_SECTIONS,
  LEGACY_CANONICAL_TO_FAMILY,
  type CanonicalTrackerFamily,
  type HomepageSectionId,
} from "./canonicalTrackerFamilies.generated";

export {
  CANONICAL_TRACKER_FAMILIES,
  HOMEPAGE_SECTIONS,
  LEGACY_CANONICAL_TO_FAMILY,
  POPULAR_THIS_WEEK,
  POPULAR_THIS_WEEK_WEEK,
} from "./canonicalTrackerFamilies.generated";

export type {
  CanonicalTrackerFamily,
  HomepageSection,
  HomepageSectionId,
  PopularThisWeekEntry,
  PopularThisWeekStore,
} from "./canonicalTrackerFamilies.generated";

export function getTrackerFamily(id: string): CanonicalTrackerFamily | undefined {
  return CANONICAL_TRACKER_FAMILIES.find((family) => family.id === id);
}

export function resolveFamilyId(id: string): string {
  return LEGACY_CANONICAL_TO_FAMILY[id] ?? id;
}

export function familiesForSection(
  sectionId: HomepageSectionId,
): CanonicalTrackerFamily[] {
  return CANONICAL_TRACKER_FAMILIES.filter(
    (family) => family.homepageSection === sectionId,
  ).sort((a, b) => a.displayOrder - b.displayOrder);
}

export function familyDisplayOrder(id: string): number {
  return getTrackerFamily(resolveFamilyId(id))?.displayOrder ?? 999;
}

export function familyHomepageSection(id: string): HomepageSectionId | undefined {
  return getTrackerFamily(resolveFamilyId(id))?.homepageSection;
}

/** User-facing title; never expose internal ids. */
export function familyDisplayName(id: string): string {
  const family = getTrackerFamily(resolveFamilyId(id));
  return family?.displayName ?? "Tracked item";
}

export function familySubtitle(id: string): string | undefined {
  return getTrackerFamily(resolveFamilyId(id))?.subtitle;
}

import { render, screen, fireEvent } from "@testing-library/react";
import { SwipeCard } from "./SwipeCard";
import type { JobCard } from "@/lib/types";

// Mock framer-motion to avoid JSDOM animation issues
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, onDragEnd, style, ...rest }: any) => (
      <div
        {...rest}
        onPointerUp={(e: any) => {
          // Simulate drag end with the accumulated offset from data attributes
          const offsetX = parseInt(e.currentTarget.dataset.dragOffsetX || "0", 10);
          if (onDragEnd) onDragEnd(e, { offset: { x: offsetX } });
        }}
      >
        {children}
      </div>
    ),
  },
  useMotionValue: () => ({ get: () => 0, set: () => {} }),
  useTransform: () => 0,
  AnimatePresence: ({ children }: any) => children,
}));

const mockJob: JobCard = {
  id: "job-1",
  title: "Senior Backend Engineer",
  company_id: "company-1",
  description: "Build great things",
  required_skills: ["Python", "FastAPI", "PostgreSQL"],
  salary_min: 120_000,
  salary_max: 160_000,
  location: "New York",
  remote_ok: true,
  seniority: "Senior",
};

test("calls onSwipe('right') when dragged past the right threshold", () => {
  const onSwipe = jest.fn();
  render(<SwipeCard job={mockJob} onSwipe={onSwipe} />);

  const card = screen.getByTestId("swipe-card");

  // Simulate a right-swipe drag sequence
  fireEvent.pointerDown(card, { clientX: 0 });
  fireEvent.pointerMove(card, { clientX: 150 });

  // Set the mock drag offset and trigger pointerUp
  card.dataset.dragOffsetX = "150";
  fireEvent.pointerUp(card);

  expect(onSwipe).toHaveBeenCalledWith("right");
});

test("calls onSwipe('left') when dragged past the left threshold", () => {
  const onSwipe = jest.fn();
  render(<SwipeCard job={mockJob} onSwipe={onSwipe} />);

  const card = screen.getByTestId("swipe-card");
  card.dataset.dragOffsetX = "-150";
  fireEvent.pointerUp(card);

  expect(onSwipe).toHaveBeenCalledWith("left");
});

test("does not call onSwipe when drag is below threshold", () => {
  const onSwipe = jest.fn();
  render(<SwipeCard job={mockJob} onSwipe={onSwipe} />);

  const card = screen.getByTestId("swipe-card");
  card.dataset.dragOffsetX = "50";
  fireEvent.pointerUp(card);

  expect(onSwipe).not.toHaveBeenCalled();
});

test("renders salary range and top skill tags on the card", () => {
  render(<SwipeCard job={mockJob} onSwipe={jest.fn()} />);
  expect(screen.getByText(/\$120,000/)).toBeInTheDocument();
  expect(screen.getAllByTestId("skill-tag")).toHaveLength(mockJob.required_skills!.length);
});

test("renders job title", () => {
  render(<SwipeCard job={mockJob} onSwipe={jest.fn()} />);
  expect(screen.getByText("Senior Backend Engineer")).toBeInTheDocument();
});

test("renders remote OK indicator when job is remote", () => {
  render(<SwipeCard job={mockJob} onSwipe={jest.fn()} />);
  expect(screen.getByText(/Remote OK/)).toBeInTheDocument();
});
